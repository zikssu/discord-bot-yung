# yung Discord Bot

> Custom Discord community bot built with Python and `discord.py`, designed for server management, automation, and engagement features for the home community.

Bot ini dikembangkan sebagai bot modular yang memisahkan fungsionalitas ke dalam beberapa *cog* dan fitur, sehingga lebih mudah dikelola, dikembangkan, dan diperluas.

---

## Daftar Isi

- [Tentang Proyek](#tentang-proyek)
- [Fitur Utama](#fitur-utama)
- [Command yang Tersedia](#command-yang-tersedia)
- [Struktur Proyek](#struktur-proyek)
- [Teknologi yang Digunakan](#teknologi-yang-digunakan)
- [Instalasi](#instalasi)
- [Konfigurasi Environment](#konfigurasi-environment)
- [Menjalankan Bot](#menjalankan-bot)
- [Penyimpanan Data](#penyimpanan-data)
- [Arsitektur Singkat](#arsitektur-singkat)
- [Catatan Penting](#catatan-penting)

---

## Tentang Proyek

Proyek ini berfungsi sebagai bot Discord all-in-one untuk komunitas `home.`. Fokus utamanya adalah membantu pengelola server dalam:

- mengelola komunitas dan channel,
- membuat proses otomatis yang mengurangi pekerjaan manual,
- menyediakan fitur interaksi publik seperti feed, feedback, ticket, dan profil masyarakat,
- menjaga UX anggota tetap ramah dan interaktif melalui slash command.

Nama bot yang dipakai di dalam code dan UI adalah `Homi`, namun repository ini sendiri berada di project `discord-bot-yung` dan menggunakan package `yung` sebagai entry point utama.

---

## Fitur Utama

### 1. Utilitas Server
- `/ping` — mengecek latency koneksi bot.
- `/infoserver` — menampilkan informasi dasar server.
- `/infouser` — menampilkan profil member Discord.

### 2. Automasi Channel
- `/autothread` — menambahkan, menghapus, atau melihat daftar auto-thread di channel tertentu.
- `/auto-reminder` — membuat pengingat berulang otomatis di channel atau thread tertentu dengan interval menit dan opsi mention role.

### 3. Feedback & Komunikasi
- `/setup-feedback` — menyiapkan panel feedback box untuk server.
- Kritik dan saran dapat dikirim dengan modal dan diposting ke channel khusus.
- Postingan feedback dilengkapi thread komentar dan reaksi untuk evaluasi masyarakat.

### 4. Home Feed
- `/setup-feed` — mengatur channel feed dan log feed.
- `/buat-postingan` — memfasilitasi anggota untuk membuat postingan komunitas.
- Mendukung kategori seperti `Berita & Informasi` dan `Umum`.
- Dukungan media URL multi-link, upload gambar, reaksi like/dislike, serta komentar di thread.
- Tombol Like/Dislike menggunakan aset ikon di `yung/assets/feed/`; bot memerlukan izin `Manage Emojis and Stickers` dan slot emoji server yang tersedia.

### 5. Ticket System
- `/setup-ticket` — menyiapkan panel tiket dan konfigurasi channel log.
- Kategori ticket seperti `Help`, `Lady Verification`, `Partnership`, `User Report`, dan `Bug Report`.
- Memungkinkan pembuatan tiket dari panel interaktif dan log terkait manajemen tiket.

### 6. Kartu Identitas Penghuni (KIP)
- `/setup-kip` — menyiapkan panel KIP.
- Anggota dapat membuat, melihat, mengedit, dan menghapus KIP mereka.
- KIP dibuat dalam format gambar PNG berbasis PIL/Pillow dan disimpan ke channel tertentu.
- Setiap anggota hanya dapat memiliki satu KIP per server.

### 7. Moots
- `/setup-moots` — menyiapkan panel Moots.
- Anggota dapat mengunggah link Instagram, TikTok, Facebook, X, dan WhatsApp Channel.
- Profil ditampilkan dengan tombol tautan dan dapat diedit atau dihapus oleh pemiliknya.
- Bot memerlukan izin `Manage Emojis and Stickers` dan slot emoji server yang tersedia untuk membuat ikon tombol dari aset logo.

---

## Command yang Tersedia

| Command | Kategori | Fungsi | Akses |
|---|---|---|---|
| `/bantuan` | Bantuan | Menampilkan panel bantuan interaktif | Semua pengguna |
| `/ping` | Utilitas | Menampilkan latency WebSocket bot | Semua pengguna |
| `/infoserver` | Utilitas | Menampilkan informasi server | Semua pengguna |
| `/infouser` | Utilitas | Menampilkan profil pengguna Discord | Semua pengguna |
| `/autothread` | Automasi | Menambah, menghapus, atau melihat Auto Thread | `Manage Channels` |
| `/auto-reminder` | Automasi | Mengatur reminder berulang | `Manage Channels` |
| `/setup-feedback` | Administrasi | Menyiapkan panel feedback box | `Manage Channels` |
| `/setup-ticket` | Administrasi | Menyiapkan panel ticket | `Manage Channels` |
| `/setup-feed` | Administrasi | Menyiapkan panel Home Feed dan channel log | `Manage Server` |
| `/buat-postingan` | Home Feed | Membuat postingan feed | Semua pengguna |
| `/setup-kip` | Administrasi | Menyiapkan panel KIP | `Manage Server` |
| `/setup-moots` | Administrasi | Menyiapkan panel Moots | `Manage Channels` |

> Beberapa command menambahkan modal, select menu, dan button UI. Bot juga memerlukan permission yang sesuai untuk mengirim embed, membuat thread, mengelola pesan, dan memproses attachment.

---

## Struktur Proyek

```text
.
├── README.md
├── requirements.txt
├── .env.example
├── yung/
│   ├── main.py
│   └── bot/
│       ├── __init__.py
│       ├── loader.py
│       ├── store.py
│       └── commands/
│           ├── bantuan.py
│           ├── utilitas/
│           │   ├── ping.py
│           │   ├── infoserver.py
│           │   ├── infouser.py
│           │   └── common.py
│           └── automasi/
│               ├── common.py
│               ├── autothread/
│               │   ├── autothread.py
│               │   └── data/
│               ├── auto_reminder/
│               │   ├── auto_reminder.py
│               │   └── data/
│               ├── feedback/
│               │   ├── feedback.py
│               │   └── data/
│               ├── feed/
│               │   ├── feed.py
│               │   └── data/
│               ├── ticket/
│               │   ├── ticket.py
│               │   └── data/
│               ├── kip/
│               │   ├── kip.py
│               │   └── data/
│               └── moots/
│                   ├── moots.py
│                   └── data/
└── yung/assets/
    ├── fonts/
    │   └── font files for KIP rendering
    └── moots/
        ├── Instagram.png
        ├── tiktok.png
        ├── facebook.png
        ├── x.png
        └── whatsapp.png
```

Penjelasan singkat:
- `yung/main.py` adalah entry point utama bot.
- `yung/bot/loader.py` memuat semua extension/cog.
- `yung/bot/store.py` adalah helper baca/tulis file JSON untuk data fitur lokal.
- Setiap fitur memiliki folder sendiri beserta data JSON dan fungsionalitas yang terikat.

---

## Teknologi yang Digunakan

- Python 3
- `discord.py` — library utama untuk Discord API dan command framework
- `python-dotenv` — membaca variabel environment dari `.env`
- `Pillow` — menghasilkan gambar KIP dan tampilan visual untuk fitur berbasis image

Versi utama proyek saat ini: 

```txt
discord.py>=2.6,<3.0
python-dotenv>=1.0,<2.0
Pillow>=11.0
```

---

## Instalasi

### 1. Clone repository

```bash
git clone https://github.com/zikssu/discord-bot-yung.git
cd discord-bot-yung
```

### 2. Buat virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependency

```bash
pip install -r requirements.txt
```

---

## Konfigurasi Environment

Buat file `.env` di root project dengan isi berikut:

```env
DISCORD_TOKEN=TOKEN_BOT_DISCORD_KAMU
DISCORD_GUILD_ID=ID_SERVER_DISCORD_OPTIONAL
```

### Penjelasan variabel

- `DISCORD_TOKEN` — token bot Discord dari developer portal.
- `DISCORD_GUILD_ID` — ID server target untuk sync command ke guild spesifik. Jika tidak diisi, bot akan melakukan sync global.

> Penting: bot harus diundang ke server dengan permission yang sesuai serta scope `bot` dan `applications.commands`.

Contoh permission yang umum diperlukan:
- View Channels
- Send Messages
- Manage Channels
- Manage Server
- Create Public Threads
- Send Messages in Threads
- Read Message History
- Embed Links
- Attach Files
- Mention Everyone

---

## Menjalankan Bot

Dari root project, jalankan:

```bash
python yung/main.py
```

Atau jika ingin menjalankan dari folder `yung`:

```bash
cd yung
python main.py
```

Saat bot berhasil terhubung, terminal akan menampilkan indikator bahwa bot sudah online.

---

## Penyimpanan Data

Bot ini menggunakan penyimpanan lokal berbasis file JSON, bukan database eksternal. Data fitur disimpan di subfolder masing-masing fitur, misalnya:

- `yung/bot/commands/automasi/autothread/data/autothread.json`
- `yung/bot/commands/automasi/auto_reminder/data/auto_reminders.json`
- `yung/bot/commands/automasi/feed/data/feed_posts.json`
- `yung/bot/commands/automasi/feedback/data/saran.json`
- `yung/bot/commands/automasi/kip/data/kip.json`
- `yung/bot/commands/automasi/moots/data/moots.json`
- `yung/bot/commands/automasi/ticket/data/tickets.json`

Karena data tersimpan secara lokal, backup reguler sangat disarankan jika server digunakan dalam skala produksi.

---

## Arsitektur Singkat

Bot menggunakan pendekatan modular dengan extension per fitur:

- `main.py` memulai bot dan memanggil loader.
- `loader.py` memuat semua extension.
- Setiap fitur diorganisasi dalam folder independen.
- Semua logika interaksi UI (button/select/modal) berada di file fitur terkait.
- Data diakses melalui `bot/store.py` agar proses baca/tulis JSON konsisten.

Gambaran umum alur kerja:

```text
Discord Interaction
        ↓
Bot / Slash Command
        ↓
Cog / Feature Module
        ↓
JSON Storage / Discord API
```

---

## Catatan Penting

- Bot ini dibuat untuk kebutuhan komunitas `home.` dan masih dalam pengembangan modular.
- Banyak fitur mengandalkan `discord.ui` dan modal input, sehingga perlu diperhatikan struktur UI agar tetap kompatibel dengan `discord.py` versi yang dipakai.
- Jika bot tidak bisa menjalankan command tertentu, cek:
  - token valid,
  - bot sudah masuk server,
  - permission channel dan role benar,
  - file `.env` sudah dibuat.
- Untuk fitur KIP, font yang dibutuhkan berada di `yung/assets/fonts/`.
- Pastikan file data JSON dapat ditulis oleh user/process yang menjalankan bot.

---

## Ringkasan Singkat

Bot ini merupakan solusi Discord komunitas yang menekankan otomatisasi, manajemen publikasi, feedback, ticket, dan dukungan interaksi sosial yang modern. Dengan struktur modular dan basis data lokal JSON, bot ini cocok untuk server komunitas yang ingin punya sistem serbaguna tanpa kebutuhan database server tambahan.

---

## Lisensi

Proyek ini tersedia untuk kebutuhan internal komunitas dan pengembangan lebih lanjut. Untuk detail lisensi, lihat file `LICENSE` di root repository.
