package main

import (
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const videoDir = "./video"

func main() {
	// List contents of video directory
	files, err := os.ReadDir(videoDir)
	if err != nil {
		log.Printf("Error reading video directory: %v", err)
	} else {
		log.Printf("Contents of %s:", videoDir)
		for _, file := range files {
			log.Printf("- %s", file.Name())
		}
	}

	http.HandleFunc("/video/", videoHandler)
	http.Handle("/", http.FileServer(http.Dir("./static")))

	log.Println("Server started at :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func videoHandler(w http.ResponseWriter, r *http.Request) {
	videoName := strings.TrimPrefix(r.URL.Path, "/video/")
	videoPath := filepath.Join(videoDir, videoName)

	log.Printf("Requested video: %s", videoName)
	log.Printf("Looking for video at path: %s", videoPath)

	file, err := os.Open(videoPath)
	if err != nil {
		log.Printf("Error opening video file: %v", err)
		http.Error(w, "Video not Found", http.StatusNotFound)
		return
	}
	defer file.Close()

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
