# Homi — Discord Community Bot

> 🤖 **Homi** adalah custom Discord Bot berbasis **Python + `discord.py`** yang dirancang sebagai bot serbaguna (*All in One Bot*) untuk membantu mengelola, merawat, dan mengembangkan komunitas Discord **home.**. 🏡

Bot ini dikembangkan secara modular agar fitur dapat dipisahkan ke dalam beberapa *Cog*, mudah dirawat, dan relatif mudah dikembangkan kembali.

---

## 📌 Daftar Isi

- [✨ Tentang Proyek](#-tentang-proyek)
- [🚀 Fitur Utama](#-fitur-utama)
- [🧩 Daftar Slash Command](#-daftar-slash-command)
- [⚙️ Detail Fitur](#️-detail-fitur)
- [🔑 Akses, Permission & Intent](#-akses-permission--intent)
- [🗂️ Struktur Proyek](#️-struktur-proyek)
- [💾 Penyimpanan Data](#-penyimpanan-data)
- [🛠️ Teknologi](#️-teknologi)
- [📦 Instalasi](#-instalasi)
- [🔑 Konfigurasi Environment](#-konfigurasi-environment)
- [▶️ Menjalankan Bot](#️-menjalankan-bot)
- [🧱 Arsitektur Singkat](#-arsitektur-singkat)
- [🧪 Perilaku & Penanganan Error](#-perilaku--penanganan-error)
- [🔄 Pengembangan Fitur](#-pengembangan-fitur)
- [⚠️ Catatan Penting](#️-catatan-penting)
- [📄 Lisensi](#-lisensi)

---

## ✨ Tentang Proyek

**Nama:** Homi  
**Platform:** Discord  
**Bahasa:** Python  
**Library utama:** `discord.py`  
**Target penggunaan:** Community / Server Management  
**Antarmuka:** `/` (**Slash Commands**)

Homi menggunakan sistem **Discord Application Commands** sehingga pengguna berinteraksi dengan bot melalui slash command seperti `/bantuan`, `/ping`, dan `/autothread`.

> 💡 Bot dibuat dengan prefix `p!` untuk kompatibilitas `commands.Bot`, tetapi command fitur yang didaftarkan di proyek ini adalah slash command.

---

## 🚀 Fitur Utama

### 🏠 Pusat Bantuan
- `/bantuan` menyediakan panel bantuan interaktif.
- Petunjuk dipisahkan menurut kegunaan:
  - 🏠 **Beranda** — pengenalan Homi.
  - 🛠️ **Utilitas** — informasi server, pengguna, dan koneksi bot.
  - ⚙️ **Administrasi** — konfigurasi fitur server untuk pengelola.
- Navigasi kategori menggunakan **Select Menu**.
- Jawaban bantuan ditampilkan secara ephemeral.

### 🛠️ Utilitas
- 🏓 Pemeriksaan latency bot melalui `/ping`.
- 🏡 Informasi server melalui `/infoserver`.
- 👤 Informasi pengguna melalui `/infouser`.

### ⚙️ Automasi
- 🧵 Membuat **Auto Thread** pada channel tertentu.
- ⏰ Mengirim **Auto Reminder** dengan jeda pilihan dan mention Role otomatis, berulang selamanya.
- 📮 Kritik & Saran melalui formulir, thread komentar, dan reaksi.
- 📱 Home Feed dengan kategori, media/link, komentar, like/dislike, dan edit posting oleh pemilik.
- 🪪 Kartu Identitas Penghuni (KIP) yang dapat dibuat dan dikelola pemilik.
- 📲 Profil Mutualan Media Sosial dengan tombol tautan dan komentar.

### 💾 Penyimpanan
Data fitur dan konfigurasi server disimpan secara lokal menggunakan file **JSON**; tidak ada database eksternal.

---

## 🧩 Daftar Slash Command

| Command | Kategori | Fungsi | Akses |
|---|---|---|---|
| `/bantuan` | 🏠 Bantuan | Membuka pusat bantuan interaktif | Semua pengguna |
| `/ping` | 🛠️ Utilitas | Menampilkan latency WebSocket bot | Semua pengguna |
| `/infoserver` | 🛠️ Utilitas | Menampilkan informasi server | Semua pengguna |
| `/infouser` | 🛠️ Utilitas | Menampilkan informasi pengguna Discord | Semua pengguna |
| `/autothread` | ⚙️ Automasi | Menambah, menghapus, dan melihat daftar Auto Thread | `Manage Channels` |
| `/auto-reminder` | ⚙️ Automasi | Mengatur jeda pengingat berulang dan mention Role di channel aktif | `Manage Channels` |
| `/setup-feedback` | ⚙️ Administrasi | Membuat atau mengganti panel Feedback Box server | `Manage Channels` |
| `/setup-ticket` | ⚙️ Administrasi | Menyiapkan panel ticket, log, dan channel publik partnership | `Manage Channels` |
| `/setup-feed` | ⚙️ Administrasi | Menyiapkan channel panel Home Feed dan log | `Manage Server` |
| `/buat-postingan` | 📱 Home Feed | Membuka formulir untuk membuat postingan | Semua pengguna |
| `/setup-kip` | ⚙️ Administrasi | Mengirim panel Kartu Identitas Penghuni | `Manage Server` |
| `/setup-mutual-medsos` | ⚙️ Administrasi | Mengirim panel Mutualan Media Sosial | `Manage Channels` |

> 🔒 Permission pada tabel adalah **default permission command** di Discord. Bot juga memerlukan izin channel yang sesuai untuk melakukan tindakan, misalnya mengirim embed, mengelola pesan, membuat thread, dan mengunggah lampiran.

---

## ⚙️ Detail Fitur

### 🏓 `/ping`

Memeriksa latency WebSocket bot.

Respons menampilkan latency WebSocket dalam milidetik (`ms`) pada embed.

---

### 🏡 `/infoserver`

Menampilkan informasi dasar server Discord tempat command dijalankan:

- Nama server
- Server ID
- Pemilik server
- Jumlah anggota
- Tanggal pembuatan server

Command ini hanya dapat digunakan di dalam server/guild.

---

### 👤 `/infouser`

Menampilkan informasi pengguna Discord.

Jika parameter `pengguna` tidak diberikan, bot akan menampilkan informasi pengguna yang menjalankan command.

Informasi yang ditampilkan:

- Username
- User ID
- Status apakah akun merupakan bot
- Tanggal pembuatan akun
- Tanggal bergabung ke server, apabila pengguna merupakan member server

---

### 📱 Home Feed — `/setup-feed` dan `/buat-postingan`

Pengelola menjalankan `/setup-feed` dengan dua opsi channel:

| Opsi | Kegunaan |
|---|---|
| `channel` | Tempat panel dan postingan Feed diterbitkan |
| `log_channel` | Tempat bot mencatat postingan baru |

Anggota dapat memulai postingan melalui `/buat-postingan` atau tombol **Upload** di panel Feed. Pilih kategori **Berita & Informasi** atau **Umum**, lalu isi:

| Kolom | Ketentuan |
|---|---|
| Judul | Wajib; maksimal 200 karakter |
| Caption / Informasi | Wajib; maksimal 3.500 karakter |
| URL Media / Link | Opsional; maksimal 500 karakter pada kolom. Beberapa URL HTTP/HTTPS dapat dipisahkan dengan ` | `; hingga 10 URL teks |
| Upload Image | Opsional; satu file gambar. Jika dipakai, gambar masuk bersama URL teks |

Postingan menampilkan pengirim, kategori, media, dan jumlah reaksi. URL gambar pertama menjadi pratinjau gambar; tautan lain ditampilkan sebagai link. Tombol like/dislike membuat satu pilihan per pengguna dan pilihan dapat dicabut atau diganti. Pemilik postingan dapat mengedit judul, caption, dan daftar URL; tombol upload membuka formulir untuk membuat postingan tambahan. Postingan memiliki thread komentar publik yang diarsipkan otomatis setelah 24 jam.

`/setup-feed` memerlukan **Manage Server**. `/buat-postingan` dapat digunakan anggota, tetapi hanya akan berhasil jika Feed sudah dikonfigurasi administrator.

---

### 🪪 Kartu Identitas Penghuni — `/setup-kip`

Pengelola menjalankan `/setup-kip` dan memilih channel panel. Anggota menggunakan tombol pada panel:

| Tombol | Kegunaan |
|---|---|
| **Buat KIP** | Membuat satu kartu identitas untuk akun tersebut di server |
| **Lihat KIP** | Mengirim link kartu milik anggota secara ephemeral |

Form kartu meminta Nama (maksimal 80 karakter), Umur (angka 1–120), Jenis Kelamin (maksimal 30 karakter), Domisili (maksimal 100 karakter), dan Hobi (maksimal 120 karakter). Empat kolom pertama wajib diisi; Hobi opsional. Bot memberi nomor berurutan dengan format `KIP-00001`, membuat gambar kartu PNG, menerbitkannya pada channel KIP, dan membuat thread komentar publik. Panel KIP menyediakan **Buat KIP** dan **Lihat KIP**; pada kartu, pemilik memiliki tombol **Edit** dan **Hapus**. Hanya pemilik kartu yang boleh mengubah atau menghapusnya. Satu anggota hanya dapat memiliki satu KIP per server. Data yang ditampilkan pada kartu bersifat terlihat oleh anggota yang dapat melihat channel KIP; jangan masukkan informasi sensitif.

`/setup-kip` memerlukan **Manage Server**. Pembuatan gambar membutuhkan Pillow; file font untuk kartu disertakan di `homi/assets/fonts/`.

---

### 📲 Mutualan Media Sosial — `/setup-mutual-medsos`

Pengelola memilih channel untuk panel Mutualan. Anggota menekan **Upload** dan dapat mengisi tautan berikut:

- Instagram
- TikTok
- Facebook
- X
- Saluran WhatsApp

Semua kolom media sosial opsional. Jika diisi, tautan harus berupa URL lengkap yang diawali `http://` atau `https://`. Profil diterbitkan di channel Mutualan beserta avatar pengguna, tombol tautan untuk platform yang diisi, dan thread komentar. Pemilik profil dapat **Edit**, **Hapus**, atau **Upload** ulang profilnya; anggota lain tidak dapat mengedit profil tersebut.

`/setup-mutual-medsos` memerlukan **Manage Channels**. Panel perlu disiapkan sebelum anggota mengunggah profil.

---

### 🧵 `/autothread`

Satu command untuk menambah, menghapus, atau melihat daftar Auto Thread di server. Daftar konfigurasi ditampilkan dalam embed dan hanya mencakup channel pada server tempat command dijalankan.

Parameter:

| Parameter | Tipe | Keterangan |
|---|---|---|
| `aksi` | Choice | `Menambahkan (Add)`, `Menghapus (Remove)`, atau `Daftar Autothread (List)` |
| `channel` | Text Channel, opsional | Wajib untuk aksi tambah dan hapus; tidak dibutuhkan untuk daftar |
| `reaksi` | String, opsional | Satu atau lebih emoji dipisahkan menggunakan spasi |

#### ➕ Menambahkan Auto Thread

Saat channel didaftarkan:

1. Konfigurasi channel disimpan ke `bot/commands/automasi/autothread/data/autothread.json`.
2. Nama thread tetap ditetapkan sebagai `💬 Comment Section`.
3. Daftar emoji reaksi disimpan.
4. Bot memberikan konfirmasi secara ephemeral.

Contoh konsep penggunaan:

```text
/autothread
aksi: Menambahkan (Add)
channel: #diskusi
reaksi: 🔥 👍
```

Nama thread ditetapkan bot sebagai `💬 Comment Section`; nama tersebut tidak memiliki opsi command untuk dikustomisasi. Setelah aktif, setiap pesan baru dari pengguna di channel tersebut akan diproses oleh listener Auto Thread.

#### ➖ Menghapus Auto Thread

Dengan aksi `Menghapus (Remove)`, konfigurasi channel akan dihapus dari penyimpanan JSON.

#### 📋 Melihat daftar Auto Thread

Pilih aksi `Daftar Autothread (List)` tanpa memilih channel. Bot mengirim embed ephemeral yang menampilkan channel, nama thread, dan seluruh reaksi otomatis tersimpan. Daftar dibatasi hingga 25 channel per embed.
---

### ⏰ `/auto-reminder`

Command ini mengelola pengingat di channel tempat command dijalankan. Bot mengirim pengingat pertama setelah jeda yang dipilih, lalu mengulanginya dengan jeda yang sama tanpa batas waktu. Role opsional akan di-mention pada setiap pengiriman. Jadwal tetap tersimpan setelah bot dimulai ulang.

| Parameter | Keterangan |
|---|---|
| `aksi` | `Tambah`, `Hapus`, atau `Daftar` |
| `pesan` | Isi pengingat, wajib untuk aksi tambah. Command harus dijalankan di channel tujuan |
| `jeda_waktu_menit` | Jarak antar-pengingat dalam menit, 1–525600; default `1440` (24 jam). Contoh: `60` = 1 jam |
| `tag` | Role Discord opsional untuk di-mention setiap kali pengingat dikirim |
| `id_pengingat` | ID yang ditampilkan dalam daftar, wajib untuk aksi hapus |

Contoh mengatur pengingat berulang setiap 2 jam di channel saat ini dan meng-mention Role yang dipilih:

```text
/auto-reminder
aksi: Tambah
pesan: Jangan lupa cek pengumuman terbaru!
jeda_waktu_menit: 120
tag: @Penghuni
```

Jeda yang dipilih berlaku sejak pengingat dibuat dan setelah setiap pengiriman. `Daftar` menampilkan pengingat untuk server ini; `Hapus` menghentikan pengingat dengan ID yang dipilih. Hanya Role yang dipilih yang di-mention; mention lain dalam isi pesan tidak dipicu. Pengelolaan command memerlukan **Manage Channels**. Konfigurasi tersimpan di `bot/commands/automasi/auto_reminder/data/auto_reminders.json`.

#### Membuat pengingat dari sebuah post

Pada post yang ingin diingatkan, klik kanan (desktop) atau tekan menu `⋯` (mobile), lalu pilih **Apps → Auto Reminder dari Post**. Link post akan terisi otomatis; atur jeda dan pilih Role opsional. Pengingat dikirim ke channel/thread post dengan jeda itu tanpa batas waktu.

| Kolom form | Cara mengisi |
|---|---|
| `Link Post` | Link post terisi otomatis |
| `Jeda Waktu (menit)` | Jarak antar-reminder; default `1440` (24 jam). Contoh `60` untuk setiap 1 jam |
| `Tag Role (opsional)` | Pilih Role yang akan di-mention di setiap reminder |

Pengiriman pertama dilakukan setelah jeda yang dipilih, kemudian berulang selamanya sampai pengingat dihapus.

---

### 🧵 Auto Thread Listener

Fitur Auto Thread berjalan melalui event:

```python
on_message
```

Bot akan mengabaikan:

- Pesan yang bukan berasal dari guild.
- Pesan dari bot lain.
- Pesan pada channel yang bukan `TextChannel`.
- Channel yang tidak terdaftar sebagai Auto Thread.

Untuk pesan yang memenuhi kondisi:

1. Bot membuat thread baru.
2. Nama thread menggunakan nama default `💬 Comment Section`.
3. Thread menggunakan `auto_archive_duration=1440`.
4. Bot mencoba menambahkan seluruh emoji yang tersimpan pada konfigurasi channel.

> ℹ️ `1440` menit = **24 jam**.

---

### 📮 `/setup-feedback`

Membuat panel **Feedback Box** pada channel yang dipilih.
Panel dan setiap masukan yang dikirim akan menampilkan banner server. Avatar profil pengirim juga ditampilkan pada embed setiap masukan.

Panel menyediakan tiga tombol:

| Tombol | Fungsi |
|---|---|
| 💡 **Kirim Saran** | Membuka formulir untuk mengirim saran |
| 🗣️ **Kirim Kritik** | Membuka formulir untuk mengirim kritik |
| ⭐ **Kirim Rating** | Membuka formulir khusus dengan kolom Rating (1–5) dan Alasan |

Ketiga tombol Kirim juga tersedia di bawah setiap kiriman, bersama tombol **Edit**. Hanya pemilik kiriman yang dapat mengubahnya.
Deskripsi utama ditampilkan sebagai blockquote (`> `) di atas field inline. Kiriman Saran/Kritik menampilkan Pengirim dan Tipe, sedangkan kiriman Rating menampilkan Pengirim dan Rating dengan satu jarak setelah deskripsi.

Konfigurasi channel disimpan berdasarkan:

- `guildId`
- `channelId`
- `panelMessageId`

Jika `/setup-feedback` dijalankan kembali pada channel yang sama, panel yang ada akan diperbarui, bukan mengirim panel baru. Duplikat panel lama dari bot pada channel tersebut juga dibersihkan.

---

### 🎫 `/setup-ticket`

Jalankan `/setup-ticket` dan pilih channel panel/thread serta channel log khusus. Setelah itu, pilih channel publik partnership dari dropdown pada pesan ephemeral **Setup panel tiket**. Command ini tidak membuat Discord Category baru. Anggota memilih kategori dari dropdown langsung pada panel; setiap pilihan membuat private thread bernama `NOMOR-KATEGORI-USERNAME`. Panel tidak menampilkan daftar kategori di deskripsinya.

Kategori Help langsung membuka formulir **Keperluan apa yang penting?** dan jawaban tampil pada ticket. Tombol **Tutup Ticket** dapat digunakan pembuat ticket atau staf terkait, sedangkan tombol **Hapus** hanya dapat digunakan staf role yang menangani kategori ticket itu.

Pada ticket Partnership, tombol **Masukkan Teks** membuka formulir Nama Server, Teks Partnership, User ID perwakilan, dan Link Invite. User ID otomatis terisi dengan ID pengirim; Link Invite otomatis diambil dari teks partnership bila ditemukan. Partnership Manager (role `1556885212640710686`) dapat menekan **Accept** atau **Tolak** pada pengajuan. Jika disetujui, embed partnership dikirim ke channel publik yang dipilih saat setup, dengan ping role `1557922621386137600`. Nama server tampil sebagai Author, teks partnership menjadi deskripsi, lalu perwakilan dan link `[Nama Server](invite)` tampil di bawah teks. Thumbnail server diambil dari invite bila Discord menyediakan metadata; tombol Join Server muncul bila invite tersedia.

Log ticket dibuka dan ditutup dikirim ke channel log yang dipilih. Konfigurasi disimpan di `bot/commands/automasi/ticket/data/ticket_settings.json`, sedangkan ticket yang masih aktif disimpan di `bot/commands/automasi/ticket/data/tickets.json`. Nomor ticket berurutan per server.

Bot memerlukan izin **Create Private Threads**, **Send Messages in Threads**, dan **Manage Threads** pada channel ticket, serta izin mengirim pesan/embed pada channel panel, log, dan partnership. Bot menambahkan anggota staf yang tersedia di cache guild ke private thread. Konfigurasi bot saat ini tidak mengaktifkan privileged **Server Members Intent**, sehingga cache bisa belum mencakup seluruh anggota role. Untuk memastikan semua staf dapat mengakses private thread, aktifkan `intents.members` pada bot dan **Server Members Intent** di Discord Developer Portal.

---

### 💡 Alur Kritik & Saran

Alur fitur:

```text
👤 Pengguna
    │
    ▼
📮 Panel Kritik & Saran
    │
    ├── 💡 Kirim Saran
    │
    ├── 🗣️ Kirim Kritik
    │
    └── ⭐ Kirim Rating
             │
             ▼
        📝 Form terpisah
             ├── Saran/Kritik: isi masukan
             └── Rating: nilai 1–5 dan alasan
                    │
                    ▼
               📌 Embed Publik
                    │
             ┌──────┴──────┐
             ▼             ▼
           ⬆️ Reaksi      ⬇️ Reaksi
             │
             ▼
          💬 Thread Komentar
```

Setelah formulir dikirim:

1. Bot mencari channel Kotak Saran yang dikonfigurasi untuk guild.
2. Isi masukan diformat sebagai blockquote.
3. Bot mengirim masukan sebagai Embed.
4. Bot membuat thread komentar pada postingan.
5. Bot menambahkan reaksi `⬆️` dan `⬇️`.
6. Pengirim menerima respons ephemeral berisi link postingan dan thread komentar.

---

## 🗂️ Struktur Proyek

```text
bot-discord-kampung-halaman-paktukang-python/
│
├── .gitignore
├── README.md
│
└── homi/
    │
    ├── requirements.txt
    ├── main.py
    ├── assets/
    │   └── fonts/
    │       ├── DejaVuSans*.ttf
    │       ├── NotoSans-*.ttf
    │       └── Poppins-*.ttf
    │
    ├── bot/
    │   ├── __init__.py
    │   ├── loader.py
    │   ├── store.py
    │   │
    │   └── commands/
    │       ├── __init__.py
    │       ├── bantuan.py
    │       ├── utilitas/
    │       │   ├── __init__.py
    │       │   ├── common.py
    │       │   ├── infoserver.py
    │       │   ├── infouser.py
    │       │   └── ping.py
    │       └── automasi/
    │           ├── __init__.py
    │           ├── common.py
    │           ├── autothread/
    │           │   ├── __init__.py
    │           │   ├── autothread.py
    │           │   └── data/
    │           │       └── autothread.json
    │           ├── auto_reminder/
    │           │   ├── __init__.py
    │           │   ├── auto_reminder.py
    │           │   └── data/
    │           │       └── auto_reminders.json
    │           ├── feedback/
    │           │   ├── __init__.py
    │           │   ├── feedback.py
    │           │   └── data/
    │           │       └── saran.json
    │           ├── feed/
    │           │   ├── __init__.py
    │           │   ├── feed.py
    │           │   └── data/
    │           │       ├── feed_posts.json
    │           │       └── feed_settings.json
    │           ├── kip/
    │           │   ├── __init__.py
    │           │   ├── kip.py
    │           │   └── data/
    │           │       ├── kip.json
    │           │       └── kip_settings.json
    │           └── mutualan/
    │               ├── __init__.py
    │               ├── mutualan.py
    │               └── data/
    │                   ├── mutual_medsos.json
    │                   └── mutual_medsos_settings.json
    │
```

File command dan data setiap fitur automasi sekarang dikelompokkan di folder fitur masing-masing. Data automasi dibaca dan ditulis di subfolder `data/` di samping file command.

### 📄 Penjelasan File

#### `main.py`
Entry point aplikasi.

Tugas utamanya:

- Memuat environment variable.
- Membuat Discord intents.
- Membuat instance `PakTukang`.
- Memuat seluruh extension/Cog.
- Melakukan sinkronisasi slash command.
- Menjalankan bot menggunakan token.

#### `bot/loader.py`
Menjadi extension loader.

Extension yang dimuat:

```text
bot.commands.bantuan
bot.commands.utilitas.ping
bot.commands.utilitas.infoserver
bot.commands.utilitas.infouser
bot.commands.automasi.autothread.autothread
bot.commands.automasi.auto_reminder.auto_reminder
bot.commands.automasi.feedback.feedback
bot.commands.automasi.feed.feed
bot.commands.automasi.kip.kip
bot.commands.automasi.mutualan.mutualan
```

Setiap kelompok fitur automasi dimuat sebagai extension/Cog tersendiri dan dapat dikembangkan secara terpisah.

#### `bot/store.py`
Menangani penyimpanan JSON lokal.

Fungsi utama:

- `read()` → membaca data JSON.
- `write()` → menulis data JSON.

Folder penyimpanan dibuat otomatis apabila belum tersedia.

#### `bot/commands/bantuan.py`
Berisi:

- `/bantuan`
- `HelpSelect`
- `HelpView`
- Embed bantuan berdasarkan kategori.

#### `bot/commands/utilitas/`
Setiap command utilitas dimuat dari extension tersendiri:

- `ping.py` — `/ping`
- `infoserver.py` — `/infoserver`
- `infouser.py` — `/infouser`

#### `bot/commands/automasi/`
Setiap fitur memiliki folder sendiri yang berisi extension dan data:

- `autothread/autothread.py` dan `autothread/data/autothread.json`.
- `auto_reminder/auto_reminder.py` dan `auto_reminder/data/auto_reminders.json`.
- `feedback/feedback.py` dan `feedback/data/saran.json`.
- `feed/feed.py` dan file JSON di `feed/data/`.
- `ticket/ticket.py`, `ticket/data/ticket_settings.json`, dan `ticket/data/tickets.json`.
- `kip/kip.py` dan file JSON di `kip/data/`.
- `mutualan/mutualan.py` dan file JSON di `mutualan/data/`.
- `common.py` menyimpan konstanta tampilan yang dipakai lintas fitur.

---

## 💾 Penyimpanan Data

Homi menggunakan **JSON storage**, bukan database SQL/NoSQL.

### `bot/commands/automasi/autothread/data/autothread.json`

Menyimpan konfigurasi Auto Thread.

Format datanya berupa array object:

```json
[
  {
    "channelId": "123456789012345678",
    "threadName": "💬 Comment Section",
    "reactions": ["🔥", "👍"]
  }
]
```

Field:

| Field | Fungsi |
|---|---|
| `channelId` | ID channel target |
| `threadName` | Nama thread yang dibuat |
| `reactions` | Daftar emoji otomatis |

---

### `bot/commands/automasi/feedback/data/saran.json`

Menyimpan channel Kotak Saran berdasarkan server.

Format:

```json
[
  {
    "guildId": "123456789012345678",
    "channelId": "987654321098765432"
  }
]
```

Field:

| Field | Fungsi |
|---|---|
| `guildId` | ID server Discord |
| `channelId` | ID channel Kotak Saran |

### Berkas data lainnya

| File | Isi |
|---|---|
| `auto_reminder/data/auto_reminders.json` | Jadwal pengingat dan pengaturan mention Role |
| `feed/data/feed_settings.json` | Channel Feed, channel log, dan pesan panel per server |
| `feed/data/feed_posts.json` | Postingan Feed, pemilik, kategori, media, komentar, dan reaksi |
| `kip/data/kip_settings.json` | Channel panel KIP per server |
| `kip/data/kip.json` | Data KIP dan referensi pesan/thread kartu |
| `mutualan/data/mutual_medsos_settings.json` | Channel panel Mutualan per server |
| `mutualan/data/mutual_medsos.json` | Tautan sosial dan referensi profil/thread anggota |

Semua berkas dibaca dan ditulis melalui `bot/store.py`; data automasi disimpan di folder `data/` dalam folder command fitur masing-masing. Saat upgrade, jika file tujuan belum ada, helper akan mencari data di lokasi fitur sebelumnya (`homi/data/<fitur>/`) atau lokasi lama langsung di `homi/data/`, lalu menyalin isi JSON ke lokasi baru. Berkas lama dibiarkan sebagai cadangan. Saat data belum ada, helper membuat berkas dengan nilai default. JSON rusak perlu dipulihkan dari cadangan. Berkas berisi ID Discord serta data profil/pesan; jangan membagikan data produksi atau memasukkannya ke repository publik.

---

## 🔑 Akses, Permission & Intent

### Discord Intents

Kode mengaktifkan intents guild, pesan guild, dan isi pesan:

```python
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
```

Aktifkan **Message Content Intent** pada Discord Developer Portal agar konfigurasi gateway sesuai. Auto Thread memproses event pesan, tetapi tidak membaca isi teksnya; Message Content Intent diaktifkan pada konfigurasi bot untuk akses message content bila dibutuhkan.

### Permission default command

| Permission Discord | Command |
|---|---|
| **Manage Channels** | `/autothread`, `/setup-feedback`, `/setup-mutual-medsos`, `/setup-ticket` |
| **Manage Server** | `/setup-feed`, `/setup-kip` |
| Tidak dibatasi permission default | `/bantuan`, `/ping`, `/infoserver`, `/infouser`, `/buat-postingan` |

Daftar tersebut adalah permission default yang disetel pada application command. Selain itu, bot memerlukan permission sesuai tindakan dan channel tempat fitur berjalan. Secara umum, beri bot:

- **View Channel** dan **Send Messages** pada channel panel, Feed, KIP, dan Mutualan yang relevan.
- **Embed Links** untuk panel dan tampilan informasi.
- **Attach Files** untuk upload gambar dan kartu KIP.
- **Create Public Threads** dan **Send Messages in Threads** untuk komentar Feed, KIP, Mutualan, Kotak Saran, serta Auto Thread.
- **Add Reactions** untuk voting Kritik & Saran serta reaksi Auto Thread.
- Kemampuan menghapus pesan bot dan mengelola thread untuk menghapus panel atau kartu.

Sesuaikan izin bot dan role anggota untuk channel sensitif.

Untuk mengundang bot ke server, pastikan instalasi aplikasi menyertakan scope `bot` dan `applications.commands`.

---

## 🛠️ Teknologi

| Teknologi | Peran |
|---|---|
| 🐍 **Python** | Bahasa pemrograman |
| 🤖 **discord.py** | Framework/library Discord API |
| 🔐 **python-dotenv** | Memuat konfigurasi dari `.env` |
| 📦 **JSON** | Penyimpanan konfigurasi lokal |
| ⚡ **Discord Application Commands** | Sistem Slash Command |
| 🧩 **Discord Cogs/Extensions** | Modularisasi fitur |

Versi dependency utama:

```text
discord.py >= 2.6, < 3.0
python-dotenv >= 1.0, < 2.0
Pillow >= 11.0
```

`Pillow` digunakan untuk membuat gambar KIP. `aiohttp` dipakai oleh implementasi pengambilan avatar dan dipasang sebagai dependency transitif discord.py.

---

## 📦 Instalasi

### 1. Masuk ke direktori aplikasi

File entry point dan `requirements.txt` berada di dalam `homi/`:

```bash
cd homi
```

### 2. Buat Virtual Environment

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependency

```bash
python -m pip install -r requirements.txt
```

---

## 🔑 Konfigurasi Environment

Buat file `homi/.env` (dari direktori aplikasi `homi/`):

```text
.env
```

Contoh:

```env
DISCORD_TOKEN=TOKEN_BOT_DISCORD_KAMU
DISCORD_GUILD_ID=ID_SERVER_DISCORD
```

### `DISCORD_TOKEN`

Token autentikasi bot Discord.

> 🚨 **JANGAN PERNAH** memasukkan token bot ke repository publik, screenshot, README, atau membagikannya kepada orang lain.

### `DISCORD_GUILD_ID`

ID server/guild yang digunakan untuk sinkronisasi command.

Jika variable ini tersedia, bot melakukan sinkronisasi command ke guild tersebut:

```python
self.tree.copy_global_to(guild=guild)
await self.tree.sync(guild=guild)
```

Jika variable tidak tersedia, bot melakukan global sync:

```python
await self.tree.sync()
```

> 💡 Untuk pengembangan, sinkronisasi ke guild tertentu biasanya lebih praktis karena perubahan command dapat diuji pada server target tanpa bergantung pada sinkronisasi global.

Setelah mengubah deklarasi nama atau parameter slash command, restart bot agar `setup_hook()` memuat ulang extension dan menyinkronkan command. Sinkronisasi global dapat membutuhkan waktu sebelum perubahan terlihat di semua server.

---

## ▶️ Menjalankan Bot

Setelah `.env` dan dependency siap:

```bash
python main.py
```

Jika berhasil, terminal akan menampilkan:

```text
Bot telah Online sebagai ...
```

Bot kemudian siap menerima slash command yang telah tersinkronisasi.

---

## 🧱 Arsitektur Singkat

Secara sederhana, alur aplikasi adalah:

```text
                    ┌───────────────────┐
                    │     main.py       │
                    │   Bot Entrypoint  │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │     loader.py     │
                    │ Load Extensions   │
                    └─────────┬─────────┘
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
      ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
      │   bantuan   │  │   utilitas  │  │  automasi   │
      │     Cog     │  │     Cog     │  │     Feed    │
      └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
             └────────────────┼────────────────┘
                              ▼
                     ┌─────────────────┐
                     │    store.py     │
                     │   JSON Storage  │
                     └────────┬────────┘
                              ▼
                     bot/commands/automasi/<fitur>/data/*.json
```

Pendekatan ini membuat kode lebih terorganisir karena:

- `main.py` fokus pada lifecycle bot.
- `loader.py` fokus pada pemuatan module.
- Setiap Cog menangani domain fitur masing-masing.
- `store.py` menangani persistence.
- `automasi/<fitur>/data/` menyimpan JSON khusus setiap fitur automasi.

---

## 🧪 Perilaku & Penanganan Error

Beberapa validasi telah diterapkan di dalam bot.

### 🧵 Auto Thread

Bot tidak akan membuat thread jika:

- Pesan berasal dari bot.
- Pesan bukan berasal dari guild.
- Channel bukan `TextChannel`.
- Channel tidak terdaftar pada konfigurasi Auto Thread.

Jika Discord API menolak pembuatan thread atau penambahan reaksi, exception `discord.HTTPException` ditangani dan error dicetak ke console.

### 📮 Kritik & Saran

Bot memeriksa:

- Apakah guild memiliki konfigurasi Kotak Saran.
- Apakah channel yang tersimpan masih dapat ditemukan.
- Apakah channel merupakan `TextChannel`.

Jika konfigurasi belum tersedia, pengguna menerima pesan:

```text
❌ Kotak Saran belum diatur oleh staf.
```

### 📱 Home Feed, KIP, dan Mutualan

- Jika tombol panel tidak merespons setelah bot dimulai ulang, pastikan extension Automasi berhasil dimuat dan persistent view terdaftar.
- Jika setup berhasil tetapi pengguna tidak dapat mengirim konten, pastikan konfigurasi channel per server masih benar dan bot dapat mengirim embed, lampiran, atau membuat thread sesuai fitur tersebut.
- KIP memerlukan Pillow serta file font di `homi/assets/fonts/`. Periksa log terminal jika pembuatan kartu atau pengambilan avatar gagal.

### 🧩 Command tidak muncul

- Pastikan bot sudah diundang dengan scope `applications.commands`.
- Periksa `DISCORD_GUILD_ID` dan proses sinkronisasi saat startup.
- Tunggu sinkronisasi global jika bot tidak menggunakan guild sync; untuk pengembangan, gunakan ID server pada `.env`.
- Periksa default permission command dan permission pengguna di server.

---

## 🔄 Pengembangan Fitur

Untuk menambahkan fitur baru, pola yang direkomendasikan adalah membuat atau memperluas **Cog**.

Contoh:

```text
bot/
└── commands/
    ├── bantuan.py
    ├── utilitas/
    │   ├── ping.py
    │   ├── infoserver.py
    │   └── infouser.py
    ├── automasi/
    │   ├── autothread/
    │   │   ├── autothread.py
    │   │   └── data/autothread.json
    │   ├── auto_reminder/
    │   │   ├── auto_reminder.py
    │   │   └── data/auto_reminders.json
    │   ├── common.py
    │   ├── feedback/feedback.py
    │   ├── feed/feed.py
    │   ├── kip/kip.py
    │   └── mutualan/mutualan.py
    └── fitur_baru.py
```

Kemudian daftarkan extension pada:

```text
bot/loader.py
```

Contoh:

```python
async def load_extensions(bot):
    for name in [
        "bot.commands.bantuan",
        "bot.commands.utilitas.ping",
        "bot.commands.utilitas.infoserver",
        "bot.commands.utilitas.infouser",
        "bot.commands.automasi.autothread.autothread",
        "bot.commands.automasi.auto_reminder.auto_reminder",
        "bot.commands.automasi.feedback.feedback",
        "bot.commands.automasi.feed.feed",
        "bot.commands.automasi.kip.kip",
        "bot.commands.automasi.mutualan.mutualan",
        "bot.commands.fitur_baru"
    ]:
        await bot.load_extension(name)
```

### 💡 Rekomendasi Pengembangan Berikutnya

Beberapa arah pengembangan yang kompatibel dengan arsitektur saat ini:

- 🗄️ Migrasi JSON → SQLite/PostgreSQL untuk skala lebih besar.
- 🧾 Sistem logging yang lebih terstruktur.
- 🛡️ Permission/role management yang lebih granular.
- 📊 Statistik penggunaan command.
- 🔔 Sistem notifikasi moderasi.
- ⚙️ Dashboard konfigurasi.
- 🌐 Konfigurasi per-guild yang lebih lengkap.
- 🧪 Automated testing untuk fungsi storage dan command logic.
- 📝 Logging error ke channel khusus administrator.

---

## ⚠️ Catatan Penting

### 🔐 Jangan Commit `.env`

File `.gitignore` sudah menyediakan aturan untuk mengecualikan `.env` dan virtual environment:

```gitignore
.env
.env.*
!.env.example

__pycache__/
*.py[cod]
.venv/
```

### 🪪 ID Discord

`guildId` dan `channelId` bukan secret seperti token, tetapi tetap merupakan data konfigurasi spesifik server. Pertimbangkan untuk tidak menyertakan konfigurasi produksi dalam repository publik.

### 📡 Discord API

Beberapa fitur bergantung pada permission dan kondisi Discord API, terutama:

- Membuat thread
- Menambahkan reaction
- Mengirim message/embed
- Menggunakan interaction/component
- Mengakses informasi guild/member

Jika fitur tertentu gagal, periksa permission bot pada channel/server terlebih dahulu.

### 💾 JSON Storage

Penyimpanan JSON cocok untuk proyek kecil hingga menengah dan konfigurasi sederhana. Untuk deployment multi-instance atau kebutuhan data yang lebih kompleks, database akan lebih tepat.

---

## 📄 Lisensi

Proyek ini sudah memiliki file **`LICENSE`** pada repository.

Untuk mengetahui ketentuan penggunaan, penyalinan, modifikasi, dan distribusi proyek secara lengkap, silakan merujuk langsung ke:

```text
LICENSE
```

> ⚖️ **Catatan:** Ketentuan yang berlaku adalah ketentuan yang tercantum di dalam file `LICENSE` pada repository ini.

---

## 👷‍♂️ Tentang Homi

**Homi** dibuat sebagai bot custom untuk ekosistem komunitas **home.**.

Konsepnya sederhana:

> 🛠️ **Membangun, merawat, dan membantu mengembangkan server Discord melalui automasi.**

Bot ini dikembangkan dengan pendekatan modular agar fitur dapat terus ditambahkan tanpa membuat seluruh project menjadi satu file besar.

---

<div align="center">

### 🏡 home. × 👷‍♂️ Homi

**Custom Discord Bot • Python • discord.py**

_Keep building. Keep improving. Keep the community alive. 🛠️_

</div>
