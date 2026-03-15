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
source=("belinda-ai.service" "belinda-ai.sh")
sha256sums=('SKIP' 'SKIP')

package() {
  # 1. Create directory
  mkdir -p "$pkgdir/opt/$pkgname"
  mkdir -p "$pkgdir/usr/bin"
  mkdir -p "$pkgdir/usr/lib/systemd/user"

  # 2. Copy project files (excluding venv and node_modules)
  cp -r "$SRCDEST/../"* "$pkgdir/opt/$pkgname/"
  rm -rf "$pkgdir/opt/$pkgname/venv"
  rm -rf "$pkgdir/opt/$pkgname/node_modules"
  rm -rf "$pkgdir/opt/$pkgname/auth_info"

  # 3. Install start script
  install -Dm755 "$srcdir/belinda-ai.sh" "$pkgdir/usr/bin/belinda-ai"

  # 4. Install systemd service (as user service)
  install -Dm644 "$srcdir/belinda-ai.service" "$pkgdir/usr/lib/systemd/user/belinda-ai.service"
}
