package main

import (
	"context"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

type contextKey string

const contextKeyUsername contextKey = "username"

// CORSMiddleware allows cross-origin requests from the web interface.
func CORSMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-Key")
		w.Header().Set("Access-Control-Max-Age", "86400")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusNoContent)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// LoggingMiddleware logs each request.
func LoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("%s %s %s", r.Method, r.URL.Path, time.Since(start))
	})
}

// JWTAuthMiddleware verifies JWT tokens for web interface routes.
func JWTAuthMiddleware(jwtSecret string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			writeJSON(w, http.StatusUnauthorized, ErrorResponse{Error: "missing Authorization header"})
			return
		}

		tokenStr := strings.TrimPrefix(authHeader, "Bearer ")
		if tokenStr == authHeader {
			writeJSON(w, http.StatusUnauthorized, ErrorResponse{Error: "invalid Authorization format, use: Bearer <token>"})
			return
		}

		token, err := jwt.Parse(tokenStr, func(t *jwt.Token) (interface{}, error) {
			if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, jwt.ErrSignatureInvalid
			}
			return []byte(jwtSecret), nil
		})
		if err != nil || !token.Valid {
			writeJSON(w, http.StatusUnauthorized, ErrorResponse{Error: "invalid or expired token"})
			return
		}

		claims, ok := token.Claims.(jwt.MapClaims)
		if !ok {
			writeJSON(w, http.StatusUnauthorized, ErrorResponse{Error: "invalid token claims"})
			return
		}

		username, _ := claims["sub"].(string)
		ctx := context.WithValue(r.Context(), contextKeyUsername, username)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// APIKeyAuthMiddleware verifies API key for Pico and backdoor routes.
func APIKeyAuthMiddleware(apiKey string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		key := r.Header.Get("X-API-Key")
		if key == "" {
			writeJSON(w, http.StatusUnauthorized, ErrorResponse{Error: "missing X-API-Key header"})
			return
		}
		if key != apiKey {
			writeJSON(w, http.StatusUnauthorized, ErrorResponse{Error: "invalid API key"})
			return
		}
		next.ServeHTTP(w, r)
	})
}

// EitherAuthMiddleware accepts either JWT or API key authentication.
// Used for endpoints that both the web interface and Pico/backdoors need.
func EitherAuthMiddleware(jwtSecret, apiKey string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Try API key first
		if key := r.Header.Get("X-API-Key"); key != "" {
			if key == apiKey {
				next.ServeHTTP(w, r)
				return
			}
			writeJSON(w, http.StatusUnauthorized, ErrorResponse{Error: "invalid API key"})
			return
		}

		// Try JWT
		authHeader := r.Header.Get("Authorization")
		if authHeader != "" {
			tokenStr := strings.TrimPrefix(authHeader, "Bearer ")
			token, err := jwt.Parse(tokenStr, func(t *jwt.Token) (interface{}, error) {
				if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
					return nil, jwt.ErrSignatureInvalid
				}
				return []byte(jwtSecret), nil
			})
			if err == nil && token.Valid {
				next.ServeHTTP(w, r)
				return
			}
		}

		writeJSON(w, http.StatusUnauthorized, ErrorResponse{Error: "authentication required (JWT or API key)"})
	})
}
