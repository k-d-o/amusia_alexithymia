FROM alpine:3.19

WORKDIR /usr/src/app

# Install Go
RUN apk add --no-cache go

# Copy the server code
COPY main.go .

# Create directories for video and static files
RUN mkdir -p video static

# Build and run the server
RUN go build -o server main.go

EXPOSE 8080

CMD ["./server"]