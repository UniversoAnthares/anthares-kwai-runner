FROM eclipse-temurin:17-jdk-jammy

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl python3 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY kwai-up/uiautomator-controller /src

RUN set -eux; \
    mkdir -p /build/stub-classes /build/classes /build/dex; \
    find /src/stubs -name '*.java' -print0 | xargs -0 javac -source 8 -target 8 -d /build/stub-classes; \
    jar cf /build/stubs.jar -C /build/stub-classes .; \
    find /src/src -name '*.java' -print0 | xargs -0 javac -source 8 -target 8 -cp /build/stubs.jar -d /build/classes; \
    curl -fsSL https://storage.googleapis.com/r8-releases/raw/8.3.37/r8.jar -o /tmp/r8.jar; \
    java -cp /tmp/r8.jar com.android.tools.r8.D8 --min-api 18 --lib /build/stubs.jar --output /build/dex /build/classes/com/anthares/kwaiup/KwaiUpUiTest.class; \
    jar cf /app/kwaiup-uiauto.jar -C /build/dex classes.dex; \
    test -s /app/kwaiup-uiauto.jar

CMD ["sh", "-c", "python3 -m http.server ${PORT:-10000} --directory /app"]
