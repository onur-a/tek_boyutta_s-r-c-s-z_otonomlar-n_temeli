"""
Sürücüsüz Araba Simülasyonu
============================
Araba, çevresine gönderdiği "sensör" ışınlarıyla (ray-casting) pist
duvarlarına olan mesafeyi ölçer ve bu bilgiye göre otonom şekilde
direksiyon/gaz kararı verir. Klasik "kendi kendine giden araba"
projelerinin temel mantığını (algıla -> karar ver -> hareket et)
basit ve anlaşılır şekilde gösterir.

Çalıştırmak için:
    pip install pygame
    python self_driving_car.py

Tuşlar:
    R - Yeniden başlat
    ESC / pencereyi kapatma - çıkış
"""

import math
import sys
import pygame

# ---------------------------------------------------------------------------
# Ayarlar
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 1000, 700
FPS = 60

TRACK_COLOR = (60, 60, 70)
BG_COLOR = (25, 25, 30)
CAR_COLOR = (0, 200, 120)
SENSOR_COLOR = (255, 210, 0)
WALL_COLOR = (200, 60, 60)
TEXT_COLOR = (230, 230, 230)

CAR_LENGTH = 22
CAR_WIDTH = 12
MAX_SPEED = 4.5
MIN_SPEED = 1.2
ACCEL = 0.06
TURN_SPEED = 3.2          # derece / frame
SENSOR_RANGE = 220
SENSOR_ANGLES = [-90, -45, -20, 0, 20, 45, 90]  # araca göre açılar


# ---------------------------------------------------------------------------
# Pist üretimi: yuvarlak köşeli dikdörtgen (stadyum) şeklinde, sabit
# genişlikli, kendiyle kesişmeyen bir pist üretir.
# ---------------------------------------------------------------------------
def _rounded_rect_points(cx, cy, half_w, half_h, corner_r, arc_segs=16):
    """Köşe merkezleri + yay açılarıyla, saat yönünde kapalı bir yuvarlak
    dikdörtgen üretir. Düz kenarlar, ardışık yayların uç noktaları aynı
    x/y'yi paylaştığı için otomatik olarak oluşur."""
    corners = [
        (cx - half_w + corner_r, cy - half_h + corner_r, 180, 270),  # sol-üst
        (cx + half_w - corner_r, cy - half_h + corner_r, 270, 360),  # sağ-üst
        (cx + half_w - corner_r, cy + half_h - corner_r, 0, 90),     # sağ-alt
        (cx - half_w + corner_r, cy + half_h - corner_r, 90, 180),   # sol-alt
    ]
    pts = []
    for ox, oy, a0, a1 in corners:
        for i in range(arc_segs + 1):
            t = math.radians(a0 + (a1 - a0) * i / arc_segs)
            pts.append((ox + corner_r * math.cos(t), oy + corner_r * math.sin(t)))
    return pts


def build_track(cx, cy, half_w=350, half_h=200, corner_r=140, ring_width=110):
    lane_half = ring_width / 2
    outer = _rounded_rect_points(cx, cy, half_w + lane_half, half_h + lane_half,
                                  corner_r + lane_half)
    inner = _rounded_rect_points(cx, cy, half_w - lane_half, half_h - lane_half,
                                  corner_r - lane_half)
    return outer, inner


def segments_from_loop(loop):
    return [(loop[i], loop[(i + 1) % len(loop)]) for i in range(len(loop))]


# ---------------------------------------------------------------------------
# Geometri yardımcıları
# ---------------------------------------------------------------------------
def ray_segment_intersection(ray_origin, ray_dir, seg_a, seg_b):
    """Bir ışının (origin + t*dir) bir doğru parçasıyla kesişimini bulur."""
    x1, y1 = seg_a
    x2, y2 = seg_b
    x3, y3 = ray_origin
    x4, y4 = ray_origin[0] + ray_dir[0], ray_origin[1] + ray_dir[1]

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-9:
        return None

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = ((x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)) / denom

    if 0 <= t <= 1 and u >= 0:
        px = x1 + t * (x2 - x1)
        py = y1 + t * (y2 - y1)
        return (px, py), u  # u = ışın üzerindeki mesafe ölçeği
    return None


def point_segment_distance(p, a, b):
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


# ---------------------------------------------------------------------------
# Araba sınıfı
# ---------------------------------------------------------------------------
class Car:
    def __init__(self, x, y, angle):
        self.start = (x, y, angle)
        self.reset()

    def reset(self):
        self.x, self.y, self.angle = self.start
        self.speed = MIN_SPEED
        self.alive = True
        self.sensor_readings = []
        self.laps_survived_frames = 0

    def sensors(self, wall_segments):
        readings = []
        for rel_angle in SENSOR_ANGLES:
            a = math.radians(self.angle + rel_angle)
            direction = (math.cos(a), math.sin(a))
            closest_dist = SENSOR_RANGE
            closest_pt = (self.x + direction[0] * SENSOR_RANGE,
                          self.y + direction[1] * SENSOR_RANGE)
            for seg_a, seg_b in wall_segments:
                hit = ray_segment_intersection((self.x, self.y), direction, seg_a, seg_b)
                if hit:
                    pt, u = hit
                    dist = u * math.hypot(*direction) * 1.0
                    # u burada gerçek ışın parametresi değil, dir normalize
                    # edilmiş olduğundan dist == mesafe (yaklaşık)
                    real_dist = math.hypot(pt[0] - self.x, pt[1] - self.y)
                    if real_dist < closest_dist:
                        closest_dist = real_dist
                        closest_pt = pt
            readings.append((closest_dist, closest_pt))
        self.sensor_readings = readings
        return readings

    def drive_ai(self, wall_segments):
        """Basit kural tabanlı otonom sürüş mantığı."""
        readings = self.sensors(wall_segments)
        dists = [d for d, _ in readings]
        left90, left45, left20, front, right20, right45, right90 = dists

        # Direksiyon: hangi taraf daha dar ise diğer tarafa (açık olana) dön
        steer = 0.0
        steer += (right45 - left45) * 0.02
        steer += (right20 - left20) * 0.035
        steer += (right90 - left90) * 0.01
        steer = max(-1, min(1, steer))
        self.angle += steer * TURN_SPEED

        # Hız: önü açıksa hızlan, daralıyorsa yavaşla
        if front < 60:
            self.speed -= ACCEL * 2.2
        elif front < 110:
            self.speed -= ACCEL * 0.5
        else:
            self.speed += ACCEL
        self.speed = max(MIN_SPEED, min(MAX_SPEED, self.speed))

    def move(self):
        a = math.radians(self.angle)
        self.x += math.cos(a) * self.speed
        self.y += math.sin(a) * self.speed
        self.laps_survived_frames += 1

    def corners(self):
        a = math.radians(self.angle)
        cos_a, sin_a = math.cos(a), math.sin(a)
        hl, hw = CAR_LENGTH / 2, CAR_WIDTH / 2
        pts = [(-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw)]
        out = []
        for lx, ly in pts:
            rx = lx * cos_a - ly * sin_a
            ry = lx * sin_a + ly * cos_a
            out.append((self.x + rx, self.y + ry))
        return out

    def check_crash(self, wall_segments):
        # Araç merkezinin herhangi bir duvara olan mesafesi çok azsa çarpışma say
        for seg_a, seg_b in wall_segments:
            if point_segment_distance((self.x, self.y), seg_a, seg_b) < CAR_WIDTH / 2:
                self.alive = False
                return True
        return False


# ---------------------------------------------------------------------------
# Çizim yardımcıları
# ---------------------------------------------------------------------------
def draw_track(screen, outer, inner):
    pygame.draw.polygon(screen, TRACK_COLOR, outer)
    pygame.draw.polygon(screen, BG_COLOR, inner)
    pygame.draw.lines(screen, WALL_COLOR, True, outer, 2)
    pygame.draw.lines(screen, WALL_COLOR, True, inner, 2)


def draw_car(screen, car):
    pygame.draw.polygon(screen, CAR_COLOR, car.corners())
    # Sensör ışınlarını çiz
    for dist, pt in car.sensor_readings:
        pygame.draw.line(screen, SENSOR_COLOR, (car.x, car.y), pt, 1)
        pygame.draw.circle(screen, SENSOR_COLOR, (int(pt[0]), int(pt[1])), 3)


def draw_hud(screen, font, car, frame_count):
    lines = [
        f"Hiz: {car.speed:.2f}",
        f"Acik kalinan kare: {car.laps_survived_frames}",
        "R = yeniden baslat   ESC = cikis",
    ]
    for i, line in enumerate(lines):
        surf = font.render(line, True, TEXT_COLOR)
        screen.blit(surf, (12, 10 + i * 20))
    if not car.alive:
        msg = font.render("CARPTI! R'ye basip yeniden basla", True, (255, 90, 90))
        screen.blit(msg, (WIDTH / 2 - msg.get_width() / 2, HEIGHT / 2 - 10))


# ---------------------------------------------------------------------------
# Ana döngü
# ---------------------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Surucusuz Araba Simulasyonu")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)

    cx, cy = WIDTH / 2, HEIGHT / 2
    outer, inner = build_track(cx, cy, half_w=350, half_h=200, corner_r=140, ring_width=110)
    wall_segments = segments_from_loop(outer) + segments_from_loop(inner)

    # Alt düz kenarın ortasından, sola doğru (saat yönünde) başla
    start_x, start_y = cx, cy + 200
    car = Car(start_x, start_y, angle=180)

    frame_count = 0
    running = True
    while running:
        clock.tick(FPS)
        frame_count += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    car.reset()

        if car.alive:
            car.drive_ai(wall_segments)
            car.move()
            car.check_crash(wall_segments)
        else:
            car.sensors(wall_segments)  # sensörleri görsel olarak güncel tut

        screen.fill(BG_COLOR)
        draw_track(screen, outer, inner)
        draw_car(screen, car)
        draw_hud(screen, font, car, frame_count)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()