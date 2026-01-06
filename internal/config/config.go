package config

import (
	"os"
)

// Config holds the runtime configuration for Jarvis
type Config struct {
	RemoteDaggerAddr string
	EnableLXC        bool
	Use1Password     bool
}

// LoadFromEnv loads configuration from environment variables
func LoadFromEnv() *Config {
	return &Config{
		RemoteDaggerAddr: os.Getenv("REMOTE_DAGGER_ADDR"),
		EnableLXC:        os.Getenv("JARVIS_ENABLE_LXC") == "true",
		Use1Password:     os.Getenv("JARVIS_USE_OP") == "true",
	}
}
