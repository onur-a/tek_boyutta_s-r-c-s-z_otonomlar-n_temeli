#  2 Boyutlu Otonom Araç Simülasyonu

Bu proje, **Python** ve **Pygame** kullanılarak geliştirilmiş basit bir **2 Boyutlu Otonom Araç Simülasyonu**dur.

Araç, çevresine gönderdiği sensör ışınları (Ray Casting) sayesinde pist duvarlarına olan uzaklığı algılar ve bu verilere göre otomatik olarak direksiyon ve hız kontrolü yapar. Proje, otonom araçların temel çalışma mantığını basit ve anlaşılır bir şekilde göstermeyi amaçlamaktadır.

---

#  Özellikler

- 🚗 Tamamen otonom hareket eden araç
- 📡 Ray Casting tabanlı sensör sistemi
- 🛣️ Otomatik oluşturulan yarış pisti
- ⚡ Gerçek zamanlı hız kontrolü
- ↩️ Araç çarpışma algılama sistemi
- 🎯 Basit yapay zekâ (kural tabanlı karar verme)
- 📊 Sensör ışınlarının görsel gösterimi
- 🔄 Simülasyonu yeniden başlatabilme

---

# 🛠 Kullanılan Teknolojiler

- Python 3
- Pygame
- Math
- Sys


#  Kurulum

Öncelikle Python'un bilgisayarınızda kurulu olması gerekir.

### 1. Depoyu klonlayın

```bash
git clone https://github.com/kullaniciadi/2boyutlu-otonom-arac.git
```

veya projeyi ZIP olarak indirip çıkarabilirsiniz.

---

### 2. Gerekli kütüphaneyi yükleyin

```bash
pip install pygame
```

---

### 3. Programı çalıştırın

```bash
python 2boyutluotonom.py
```

---

# 🎮 Kontroller

| Tuş | Görev |
|------|-------|
| **R** | Simülasyonu yeniden başlatır |
| **ESC** | Programdan çıkar |

---

#  Çalışma Mantığı

Araç üzerinde toplam **7 adet sensör** bulunmaktadır.

Sensör açıları:

- -90°
- -45°
- -20°
- 0°
- 20°
- 45°
- 90°

Bu sensörler belirli bir mesafeye kadar duvarları tarar.

Her karede aşağıdaki işlemler gerçekleştirilir:

1. Sensörler duvarlara olan uzaklığı ölçer.
2. Sol ve sağ taraftaki boşluklar karşılaştırılır.
3. Direksiyon uygun yöne çevrilir.
4. Ön tarafta engel varsa araç yavaşlar.
5. Yol açıksa araç hızlanır.
6. Araç ilerler.
7. Duvara temas ederse simülasyon durur.

Bu süreç sürekli tekrar edilerek aracın pistte kendi kendine ilerlemesi sağlanır.


#  Sensör Sistemi

Projede kullanılan sensör sistemi **Ray Casting** mantığıyla çalışmaktadır.

Her sensör:

- Araç merkezinden ışın gönderir.
- Pist duvarına ilk çarptığı noktayı bulur.
- Uzaklığı hesaplar.
- Yapay zekâya karar vermesi için veri sağlar.


#  Yapay Zekâ Karar Mekanizması

Projede karmaşık bir makine öğrenmesi modeli yerine **kural tabanlı (Rule-Based AI)** yaklaşımı kullanılmıştır.

Karar mekanizması şu mantıkla çalışır:

- Sağ taraf daha açıksa sağa yönelir.
- Sol taraf daha açıksa sola yönelir.
- Ön tarafta engel varsa hız düşürülür.
- Yol açıksa hız artırılır.

Bu sayede araç herhangi bir eğitim almadan pist üzerinde hareket edebilir.

---

#  Çarpışma Algılama

Araç merkezi ile pist duvarları arasındaki mesafe sürekli hesaplanmaktadır.

Belirlenen güvenlik mesafesinin altına düşüldüğünde:

- araç durur,
- simülasyon sona erer,
- kullanıcı yeniden başlatabilir.



#  Projenin Amacı

Bu proje;

- Otonom araç mantığını öğretmek,
- Ray Casting kullanımını göstermek,
- Yapay zekâ karar mekanizmasını tanıtmak,
- Pygame ile 2B simülasyon geliştirmeyi öğretmek

amacıyla hazırlanmıştır.



#  Geliştirilebilir Özellikler

- NEAT Algoritması
- Yapay Sinir Ağları
- Genetik Algoritma
- Derin Pekiştirmeli Öğrenme (Deep Reinforcement Learning)
- Gerçek şerit algılama
- Farklı pistler
- Birden fazla araç
- Skor sistemi
- Tur sayacı
- Engeller
- Trafik işaretleri


Bu proje eğitim amaçlı geliştirilmiştir.

Python ve Pygame kullanılarak hazırlanmıştır.


Bu proje eğitim ve akademik çalışmalar kapsamında serbestçe kullanılabilir.