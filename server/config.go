package main

import (
	"fmt"
	"os"
	"strings"
)

type Config struct {
	CFAccountID  string
	CFAPIToken   string
	D1DatabaseID string
	APIKey       string
	JWTSecret    string
	Username     string
	Password     string
	Port         string
}

func LoadConfig() (*Config, error) {
	// Try loading from .env file if it exists
	loadEnvFile(".env")

	cfg := &Config{
		CFAccountID:  os.Getenv("CF_ACCOUNT_ID"),
		CFAPIToken:   os.Getenv("CF_API_TOKEN"),
		D1DatabaseID: os.Getenv("D1_DATABASE_ID"),
		APIKey:       os.Getenv("B33_API_KEY"),
		JWTSecret:    os.Getenv("B33_JWT_SECRET"),
		Username:     os.Getenv("B33_USERNAME"),
		Password:     os.Getenv("B33_PASSWORD"),
		Port:         os.Getenv("PORT"),
	}

	if cfg.Port == "" {
		cfg.Port = "8080"
	}

	// Validate required fields
	missing := []string{}
	if cfg.CFAccountID == "" {
		missing = append(missing, "CF_ACCOUNT_ID")
	}
	if cfg.CFAPIToken == "" {
		missing = append(missing, "CF_API_TOKEN")
	}
	if cfg.D1DatabaseID == "" {
		missing = append(missing, "D1_DATABASE_ID")
	}
	if cfg.APIKey == "" {
		missing = append(missing, "B33_API_KEY")
	}
	if cfg.JWTSecret == "" {
		missing = append(missing, "B33_JWT_SECRET")
	}
	if cfg.Username == "" {
		missing = append(missing, "B33_USERNAME")
	}
	if cfg.Password == "" {
		missing = append(missing, "B33_PASSWORD")
	}

	if len(missing) > 0 {
		return nil, fmt.Errorf("missing required environment variables: %s", strings.Join(missing, ", "))
	}

	return cfg, nil
}

// loadEnvFile reads a .env file and sets environment variables.
// Silently ignores if the file doesn't exist.
func loadEnvFile(path string) {
	data, err := os.ReadFile(path)
	if err != nil {
		return
	}
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		key, val, found := strings.Cut(line, "=")
		if !found {
			continue
		}
		key = strings.TrimSpace(key)
		val = strings.TrimSpace(val)
		// Don't override existing env vars
		if os.Getenv(key) == "" {
			os.Setenv(key, val)
		}
	}
}
