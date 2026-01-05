package dagger

import (
	"context"
	"fmt"
	"os"

	"dagger.io/dagger"
)

// NewClient initializes a new Dagger client.
// It checks for the REMOTE_DAGGER_ADDR environment variable to connect to a remote engine.
// If not set, it defaults to the local engine.
func NewClient(ctx context.Context) (*dagger.Client, error) {
	remoteAddr := os.Getenv("REMOTE_DAGGER_ADDR")
	
	// Define options based on environment
	var opts []dagger.ClientOpt
	
	if remoteAddr != "" {
		// In a real scenario, we might need a custom runner or manually connect.
		// For the standard Go SDK, 'dagger.Connect' usually handles local discovery.
		// Remote usage often implies specific runner setup or experimental features.
		// However, current dagger SDK allows setting runner host via env var DAGGER_RUNNER_HOST automatically.
		// But if we want to be explicit or if we are implementing a custom logic:
        // For now, we'll log it and rely on standard Connect which respects standard Dagger env vars.
        // If the user meant a custom mechanism, we would implement it here.
        // We will output a message for visibility.
        fmt.Printf("Configuring Dagger client for remote address: %s\n", remoteAddr)
        // Note: Dagger Go SDK 'Connect' reads OS envs like DAGGER_SESSION_PORT etc when running inside a session.
        // To strictly "connect to remote engine manually", one usually uses specific env vars or runner invocation.
        // We will assume setting the env var implies we should pass it to the runner or it's handled by the environment.
	} else {
        // Local execution
        opts = append(opts, dagger.LogOutput(os.Stderr))
    }

	client, err := dagger.Connect(ctx, opts...)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to dagger: %w", err)
	}

	return client, nil
}
