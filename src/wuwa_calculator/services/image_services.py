""" Serviços para manipulação de imagens de personagens. """
from enum import Enum
from pathlib import Path
import shutil


class ImageType(Enum):
    """ Tipos de imagens de personagens. """
    ICON = "icons"
    SPRITE = "sprites"
    SPLASH = "splashes"


class ImageService:
    """ Serviço para manipulação de imagens de personagens."""
    def __init__(self):
        self.default_root = Path("data/characters/")
        self.custom_root = Path("storage/user_data/custom_images")

        self.supported_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
        }

    def validate_extension(self, source_path: Path) -> str:
        """ Valida a extensão do arquivo de imagem fornecido."""
        extension = source_path.suffix.lower()

        if extension not in self.supported_extensions:
            raise ValueError(
                f"Extensão de imagem não suportada: {extension}"
            )

        return extension

    def get_image(
        self,
        character_id: str,
        image_type: ImageType
    ) -> Path:
        """ Retorna o caminho da imagem do personagem,
        verificando primeiro se há uma imagem personalizada,
        caso contrário, retorna a imagem padrão."""
        custom_dir = self.custom_root / image_type.value

        for extension in self.supported_extensions:
            custom_path = custom_dir / f"{character_id}{extension}"

            if custom_path.exists():
                return custom_path

        default_path = (
            self.default_root
            / image_type.value
            / f"{character_id}.png"
        )

        if default_path.exists():
            return default_path

        return (
            self.default_root
            / image_type.value
            / "default.png"
        )

    def set_custom_image(
        self,
        character_id: str,
        image_type: ImageType,
        source_path: Path,
    ) -> Path:
        """ Salva uma imagem personalizada para o personagem,
        substituindo a imagem padrão."""
        extension = self.validate_extension(source_path)

        destination_dir = (
            self.custom_root / image_type.value
        )

        try:
            destination_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            destination = (
                destination_dir
                / f"{character_id}{extension}"
            )

            shutil.copy2(
                source_path,
                destination
            )

        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Imagem de origem não encontrada: {source_path}"
            ) from e

        except PermissionError as e:
            raise PermissionError(
                f"Sem permissão para acessar a imagem ou "
                f"diretório de destino: {source_path}"
            ) from e

        except shutil.SameFileError as e:
            raise shutil.SameFileError(
                f"A imagem de origem e destino são o mesmo arquivo: "
                f"{source_path}"
            ) from e

        except shutil.SpecialFileError as e:
            raise ValueError(
                f"O arquivo fornecido não é uma imagem comum: "
                f"{source_path}"
            ) from e

        except OSError as e:
            raise OSError(
                f"Erro ao salvar a imagem "
                f"'{source_path}' em '{destination}': {e}"
            ) from e

        return destination
