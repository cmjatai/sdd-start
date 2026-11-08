FROM python:3.14.10-bookworm

# Agrupando variáveis de ambiente
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/root

WORKDIR ${HOME}

# 1. Instalação de dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        # RUN0_PACKAGES
        apt-utils apt-file libpq-dev build-essential pkg-config \
        autoconf automake libtool libleptonica-dev \
        libxml2-dev libjpeg-dev libssl-dev libffi-dev libxslt1-dev \
        libcairo2-dev software-properties-common graphviz graphviz-dev \
        procps nmap git vim curl jq pngquant \
        poppler-utils tzdata nginx \
        ca-certificates gnupg wget \
        # LIBRE_PACKAGES
        libreoffice \
        libreoffice-writer \
        libreoffice-java-common \
        libreoffice-core \
        libreoffice-common \
        ure hyphen-pt-br fonts-opensymbol fonts-dejavu fonts-dejavu-core fonts-dejavu-extra fonts-droid-fallback \
        fonts-dustin fonts-f500 fonts-fanwood fonts-freefont-ttf fonts-lmodern fonts-lyx fonts-sil-gentium \
        fonts-texgyre fonts-tlwg-purisa fonts-liberation fontconfig \
        # java e tesseract
        openjdk-17-jdk-headless tesseract-ocr tesseract-ocr-por && \
        # Limpeza do cache do APT para reduzir tamanho da imagem
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*

# 2. Instalação do PostgreSQL 18 Client
RUN install -d /usr/share/postgresql-common/pgdg && \
    curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc && \
    echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client-18 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 3. Compilação do Ghostscript (tudo na mesma camada para permitir a exclusão do código-fonte)
RUN mkdir -p /tmp/ghostscript && \
    cd /tmp/ghostscript && \
    wget https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10080/ghostscript-10.08.0.tar.gz && \
    tar vzxfp ghostscript-10.08.0.tar.gz && \
    cd ghostscript-10.08.0 && \
    ./configure && make && make install && \
    # Limpeza pesada: deletar a pasta onde compilamos para não gastar espaço na imagem final
    cd / && rm -rf /tmp/ghostscript

# 4. Compilação e instalação do jbig2enc (Tag 0.32)
RUN cd /tmp && \
    # Clona especificamente a tag 0.32 e sem o histórico do git (--depth 1)
    git clone -b 0.32 --depth 1 https://github.com/agl/jbig2enc.git && \
    cd jbig2enc && \
    ./autogen.sh && \
    ./configure && \
    make && \
    make install && \
    ldconfig && \
    cd / && rm -rf /tmp/jbig2enc

# 5. Configurações gerais e atualização do PIP
RUN fc-cache -fv && \
    pip install --no-cache-dir --upgrade pip setuptools && \
    rm -f /etc/nginx/conf.d/* && \
    rm -f /etc/nginx/sites-enabled/*

# 6. Instalação do Node.js 26.x
RUN curl -fsSL https://deb.nodesource.com/setup_26.x | bash - &&\
    apt-get install -y nodejs

# 7. Configuração do Poetry e desativação de ambientes virtuais automáticos
ENV POETRY_VIRTUALENVS_CREATE=false
RUN pip3 install poetry

ENV DEBIAN_FRONTEND=teletype

CMD ["python3"]

# Comandos para buildar, logar,taguear e enviar a imagem para um repositório Docker remoto
# Substitua "local-image:tagname" pelo nome e tag da imagem local
# Substitua "new-repo:tagname" pelo repositório remoto e tag desejados
# Exemplo:
# docker build -t building_foundation:0003 .
# docker login myrepo --username=<your-username> --password="<your-password>" docker.io
# docker tag building_foundation:0003 myrepo/building_foundation:0003
# docker push myrepo/building_foundation:0003
# Substitua "myrepo" pelo nome do seu repositório remoto Docker.