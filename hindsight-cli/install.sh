#!/bin/bash
set -e

# Hindsight CLI installer
# Usage: curl -sSf https://your-domain.com/install.sh | sh

REPO_URL="https://github.com/your-org/hindsight-cli"
INSTALL_DIR="${HINDSIGHT_INSTALL_DIR:-$HOME/.local/bin}"
BINARY_NAME="hindsight"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_banner() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║            HINDSIGHT CLI INSTALLER               ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Detect platform
detect_platform() {
    local os=$(uname -s)
    local arch=$(uname -m)

    case "$os" in
        Darwin)
            if [[ "$arch" == "arm64" ]] || [[ "$arch" == "aarch64" ]]; then
                echo "macos-arm64"
            elif [[ "$arch" == "x86_64" ]]; then
                echo "macos-x86_64"
            else
                print_error "Unsupported macOS architecture: $arch"
                exit 1
            fi
            ;;
        Linux)
            if [[ "$arch" == "x86_64" ]]; then
                echo "linux-x86_64"
            elif [[ "$arch" == "aarch64" ]] || [[ "$arch" == "arm64" ]]; then
                echo "linux-arm64"
            else
                print_error "Unsupported Linux architecture: $arch"
                exit 1
            fi
            ;;
        *)
            print_error "Unsupported operating system: $os"
            exit 1
            ;;
    esac
}

# Download binary
download_binary() {
    local platform=$1
    local download_url="${REPO_URL}/releases/latest/download/hindsight-${platform}"
    local tmp_file="/tmp/hindsight-$$"

    print_info "Downloading Hindsight CLI for $platform..."

    if command -v curl > /dev/null 2>&1; then
        curl -fsSL "$download_url" -o "$tmp_file"
    elif command -v wget > /dev/null 2>&1; then
        wget -q "$download_url" -O "$tmp_file"
    else
        print_error "Neither curl nor wget found. Please install one of them."
        exit 1
    fi

    echo "$tmp_file"
}

# Install binary
install_binary() {
    local tmp_file=$1

    # Create install directory if it doesn't exist
    mkdir -p "$INSTALL_DIR"

    # Move binary to install directory
    mv "$tmp_file" "$INSTALL_DIR/$BINARY_NAME"
    chmod +x "$INSTALL_DIR/$BINARY_NAME"

    print_success "Installed to: $INSTALL_DIR/$BINARY_NAME"
}

# Check if directory is in PATH
check_path() {
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        print_warning "$INSTALL_DIR is not in your PATH"
        echo ""
        echo "Add it to your PATH by adding this line to your shell profile:"
        echo ""

        # Detect shell
        if [[ -n "$BASH_VERSION" ]]; then
            echo "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.bashrc"
            echo "  source ~/.bashrc"
        elif [[ -n "$ZSH_VERSION" ]]; then
            echo "  echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.zshrc"
            echo "  source ~/.zshrc"
        else
            echo "  export PATH=\"$INSTALL_DIR:\$PATH\""
        fi
        echo ""
    fi
}

# Main installation flow
main() {
    print_banner

    # Detect platform
    platform=$(detect_platform)
    print_info "Detected platform: $platform"

    # Download binary
    tmp_file=$(download_binary "$platform")

    # Install binary
    install_binary "$tmp_file"

    # Check PATH
    check_path

    print_success "Installation complete!"
    echo ""
    print_info "Try it out: $BINARY_NAME --help"
    echo ""
    print_info "Configure the API URL:"
    echo "  export HINDSIGHT_API_URL=http://localhost:8888"
    echo ""
}

# Run installation
main
