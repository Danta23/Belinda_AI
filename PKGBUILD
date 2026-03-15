# Maintainer: Danta <danta@studio234.id>
pkgname=belinda-ai
pkgver=1.0.0
pkgrel=1
pkgdesc="WhatsApp Bot Belinda AI - Intelligent assistant with Python and Node.js bridge"
arch=('any')
url="https://github.com/danta/Belinda_AI"
license=('MIT')
depends=('python' 'nodejs' 'npm' 'ffmpeg' 'yt-dlp')
makedepends=('git')
source=("belinda-ai.service" 
        "belinda-ai.sh"
        "app.py"
        "handlers.py"
        "bridge.js"
        "package.json"
        "requirements.txt")
sha256sums=('SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP')

package() {
  # 1. Create directory
  mkdir -p "$pkgdir/opt/$pkgname"
  mkdir -p "$pkgdir/usr/bin"
  mkdir -p "$pkgdir/usr/lib/systemd/user"

  # 2. Copy project files from source
  cp "$srcdir/app.py" "$pkgdir/opt/$pkgname/"
  cp "$srcdir/handlers.py" "$pkgdir/opt/$pkgname/"
  cp "$srcdir/bridge.js" "$pkgdir/opt/$pkgname/"
  cp "$srcdir/package.json" "$pkgdir/opt/$pkgname/"
  cp "$srcdir/requirements.txt" "$pkgdir/opt/$pkgname/"

  # 3. Install start script
  install -Dm755 "$srcdir/belinda-ai.sh" "$pkgdir/usr/bin/belinda-ai"

  # 4. Install systemd service (as user service)
  install -Dm644 "$srcdir/belinda-ai.service" "$pkgdir/usr/lib/systemd/user/belinda-ai.service"
}
