#!/bin/bash
cd "$(dirname "$0")/.."

set -e  # Exit on any error

echo "🚀 Bắt đầu setup môi trường conda cho WeaHouse.."

# Kiểm tra conda có được cài đặt không
if ! command -v conda &> /dev/null; then
    echo "❌ Conda chưa được cài đặt. Vui lòng cài đặt Anaconda hoặc Miniconda trước."
    echo "📥 Tải về tại: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "✅ Conda đã được cài đặt"

# Tên môi trường
ENV_NAME="weahouse_env"

# Kiểm tra xem môi trường đã tồn tại chưa
if conda env list | grep -q "^${ENV_NAME} "; then
    echo "⚠️  Môi trường '${ENV_NAME}' đã tồn tại."
    read -p "Bạn có muốn xóa và tạo lại không? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Xóa môi trường cũ..."
        conda env remove -n ${ENV_NAME} --all -y
    else
        echo "📦 Cập nhật môi trường hiện tại..."
        conda run -n ${ENV_NAME} pip install -r requirements.txt
        echo "✅ Cập nhật hoàn tất!"
        exit 0
    fi
fi

# Tạo môi trường mới với Python 3.10
echo "🐍 Tạo môi trường conda mới với Python 3.10..."
conda create -n ${ENV_NAME} python=3.10 -y

# Cài đặt pip và upgrade
echo "📦 Cài đặt và upgrade pip..."
conda install -n ${ENV_NAME} pip -y
conda run -n ${ENV_NAME} pip install --upgrade pip

# Cài đặt các thư viện từ requirements.txt
echo "📚 Cài đặt các thư viện từ requirements.txt..."
conda run -n ${ENV_NAME} pip install -r requirements.txt

echo ""
echo "🎉 Setup hoàn tất!"
echo ""
echo "📋 Hướng dẫn sử dụng:"
echo "1. Kích hoạt môi trường: conda activate ${ENV_NAME}"
echo ""
echo "💡 Hoặc chạy trực tiếp:"
echo "   conda activate ${ENV_NAME}"
echo ""
echo "🧹 Để xóa môi trường sau này: conda env remove -n ${ENV_NAME} --all"
