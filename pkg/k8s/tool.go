package k8s

import (
	"context"
	"fmt"
	"os"
	"path/filepath"

	"dagger.io/dagger"
)

// RunKubectl executes a kubectl command inside a container.
// It mounts the local ~/.kube/config to the container.
func RunKubectl(ctx context.Context, client *dagger.Client, command string) (string, error) {
	// Identify kubeconfig path
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("failed to get home dir: %w", err)
	}
	kubeconfigPath := filepath.Join(home, ".kube", "config")

    // Read the kubeconfig file content to pass as a secret or mounted file
    // Note: Mounting the host file is the simplest for local execution.
    // For remote execution, we might need to pass it as a secret.
    // We will assume host mounting for this tool.

	// Define the container
	// Using bitnami/kubectl as a lightweight image
	container := client.Container().
		From("bitnami/kubectl:latest").
		WithMountedFile("/root/.kube/config", client.Host().File(kubeconfigPath)).
        WithExec(buildExecArgs(command))

	// Execute and get stdout
	out, err := container.Stdout(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to run kubectl: %w", err)
	}

	return out, nil
}

func buildExecArgs(command string) []string {
    // Split command string simply for this demo.
    // In production, use a proper shell parser or pass string slice cleanly.
    // Here we'll wrap in sh -c to handle args easily.
    return []string{"sh", "-c", "kubectl " + command}
}
