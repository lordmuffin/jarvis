//go:build functional

package test

import (
    "context"
    "strings"
    "testing"

    "github.com/andrewjackson/jarvis/internal/dagger"
)

func TestDaggerEcho(t *testing.T) {
    ctx := context.Background()

    // Initialize Client
    client, err := dagger.NewClient(ctx)
    if err != nil {
        t.Fatalf("Failed to create dagger client: %v", err)
    }
    defer client.Close()

    // Run a simple container
    out, err := client.Container().
        From("alpine:latest").
        WithExec([]string{"echo", "hello jarvis"}).
        Stdout(ctx)

    if err != nil {
        t.Fatalf("Failed to run container: %v", err)
    }

    if strings.TrimSpace(out) != "hello jarvis" {
        t.Errorf("Expected 'hello jarvis', got '%s'", out)
    }
}
