"""Element icon URLs for the visual team builder."""

# * EDITAVEL: adicione a URL WebP especifica de cada character_id neste mapa.
# ? Se o ID nao tiver uma URL, o TeamsTab tenta usar a imagem padrao do elemento.
CHARACTER_ELEMENT_IMAGE_URLS: dict[str, str] = {
    # "brant": "https://host-permitido/element-icons/brant-fusion.webp",
    # "verina": "https://host-permitido/element-icons/verina-spectro.webp",
}

# * EDITAVEL: fallback compartilhado quando um character_id nao tem icone proprio.
ELEMENT_IMAGE_URLS: dict[str, str] = {
    "Aero": "https://wutheringlab.com/wp-content/uploads/Wuthering-Waves-Aero.png",
    "Glacio": "https://wutheringlab.com/wp-content/uploads/Wuthering-Waves-Glacio.png",
    "Electro": "https://wutheringlab.com/wp-content/uploads/Wuthering-Waves-Electro.png",
    "Fusion": "https://wutheringlab.com/wp-content/uploads/Wuthering-Waves-Fusion.png",
    "Havoc": "https://wutheringlab.com/wp-content/uploads/Wuthering-Waves-Havoc.png",
    "Spectro": "https://wutheringlab.com/wp-content/uploads/Wuthering-Waves-Spectro.png",
}
