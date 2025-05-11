package main

import (
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const videoDir = "./videos"

func main() {
	http.HandleFunc("/video/", videoHandler)
	http.Handle("/", http.FileServer(http.Dir("./static")))

	log.Println("Server started at :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func videoHandler(w http.ResponseWriter, r *http.Request) {
	videoName := strings.TrimPrefix(r.URL.Path, "/video/")
	videoPath := filepath.Join(videoDir, videoName)

	// Check if file exists
	file, err := os.Open(videoPath)
	if err != nil {
		http.Error(w, "Video not found", http.StatusNotFound)
		return
	}
	defer file.Close()

	// Set headers
	w.Header().Set("Content-Type", "video/mp4")
	http.ServeContent(w, r, videoName, getModTime(file), file)
}

func getModTime(file *os.File) (modTimeTime time.Time) {
	stat, err := file.Stat()
	if err != nil {
		return
	}
	return stat.ModTime()
}
