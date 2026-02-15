FROM golang:1.25-alpine AS builder
WORKDIR /build
COPY server/ ./
RUN go build -o /b33-server .

FROM alpine:latest
RUN apk add --no-cache ca-certificates
WORKDIR /app
COPY --from=builder /b33-server .
COPY web/ ./web/
ENV WEB_DIR=/app/web
ENV PORT=8080
EXPOSE 8080
CMD ["./b33-server"]
