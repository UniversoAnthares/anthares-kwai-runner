# Isolated Northflank build for the legacy Go ARA control API.
# This controller currently keeps jobs in memory: do not promote as durable failover.
FROM golang:1.24-alpine AS build
WORKDIR /src
COPY anthares-remote-agent/cmd/control/main.go ./main.go
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -ldflags="-s -w" -o /out/ara-control ./main.go

FROM alpine:3.21
RUN apk add --no-cache ca-certificates && addgroup -S ara && adduser -S -G ara ara
COPY --from=build /out/ara-control /usr/local/bin/ara-control
USER ara
ENV PORT=10000
EXPOSE 10000
CMD ["/usr/local/bin/ara-control"]
