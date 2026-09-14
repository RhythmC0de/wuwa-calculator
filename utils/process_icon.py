"""Script para baixar e criar ícone circular tipo Discord."""

import sys
from pathlib import Path
from urllib.request import Request, urlopen

try:
    from PIL import Image, ImageDraw
    import numpy as np
except ImportError:
    print("[ERROR] Dependência faltando: pip install pillow numpy")
    sys.exit(1)


def fetch_image_from_url(url: str) -> Image.Image | None:
    """Baixa imagem de URL."""
    try:
        print(f"[process_icon] Baixando imagem de: {url}")
        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
        )
        with urlopen(request, timeout=10) as response:
            from io import BytesIO
            image_data = response.read()
            image = Image.open(BytesIO(image_data))
            print(f"[process_icon] Imagem carregada: {image.size} - {image.mode}")
            return image
    except Exception as e:
        print(f"[process_icon] Erro ao baixar: {e}")
        return None


def remove_background_smart(image: Image.Image) -> Image.Image:
    """Remove fundo mantendo o personagem (smart background removal)."""
    print("[process_icon] Removendo fundo...")
    
    # Converte para RGBA se necessário
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Pega pixels como array numpy
    data = np.array(image)
    
    # Identifica pixels "cinza/claro" (fundo)
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    
    # Calcula a luminância
    luminance = (0.299 * r + 0.587 * g + 0.114 * b).astype(int)
    
    # Pixeis cinza/claros (luminância > 150) viram transparentes
    threshold = 150
    mask = luminance < threshold
    
    # Mantém a transparência original onde estava
    new_alpha = a.copy()
    new_alpha[~mask] = 0  # Faz fundo transparente
    
    data[:,:,3] = new_alpha
    
    result = Image.fromarray(data, 'RGBA')
    print("[process_icon] Fundo removido com sucesso")
    return result


def create_circular_icon(image: Image.Image, size: int = 256) -> Image.Image:
    """Cria ícone circular perfeito (tipo Discord).
    
    Redimensiona e aplica máscara circular sem deixar quadrado recortado.
    """
    print(f"[process_icon] Criando ícone circular {size}x{size} (tipo Discord)...")
    
    # Redimensiona mantendo proporção
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    
    # Cria imagem quadrada com fundo transparente
    circular = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    
    # Cria máscara circular perfeita
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([0, 0, size-1, size-1], fill=255)
    
    # Centra a imagem
    offset = ((size - image.width) // 2, (size - image.height) // 2)
    circular.paste(image, offset, image)
    
    # Aplica máscara circular (remove tudo que está fora do círculo)
    circular.putalpha(mask)
    
    print(f"[process_icon] Ícone circular criado perfeitamente (sem quadrado recortado)")
    return circular


def process_icon(url: str, output_path: str = "Assets/close_icon.png", size: int = 256) -> bool:
    """Pipeline: baixa, remove background, cria circular e salva."""
    print("\n" + "="*60)
    print("GERADOR DE ÍCONE CIRCULAR TIPO DISCORD")
    print("="*60)
    
    # Baixa
    image = fetch_image_from_url(url)
    if not image:
        return False
    
    # Remove fundo
    image = remove_background_smart(image)
    
    # Cria circular
    image = create_circular_icon(image, size=size)
    
    # Salva
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, 'PNG')
    print(f"\n✅ Ícone salvo em: {output}")
    print(f"   Tamanho: {image.size} (circular perfeito)")
    print("="*60 + "\n")
    return True


if __name__ == "__main__":
    # Use assim:
    # python utils/process_icon.py <URL> [OUTPUT_PATH] [SIZE]
    
    if len(sys.argv) < 2:
        print("Uso: python utils/process_icon.py <URL> [OUTPUT_PATH] [SIZE]")
        print("\nExemplo:")
        print("  python utils/process_icon.py https://i.imgur.com/2cqxCI8.png Assets/close_icon.png 256")
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "Assets/close_icon.png"
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 256
    
    success = process_icon(url, output_path, size)
    sys.exit(0 if success else 1)


