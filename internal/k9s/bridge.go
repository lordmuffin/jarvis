package k9s

import (
	"context"
	"fmt"
	"os"
	"os/exec"
)

// Launch starts k9s with the given context
func Launch(ctx context.Context, kubeconfigPath, namespace string) error {
	cmdPath, err := exec.LookPath("k9s")
	if err != nil {
		return fmt.Errorf("k9s binary not found in PATH: %w", err)
	}

	cmd := exec.CommandContext(ctx, cmdPath)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	
	if kubeconfigPath != "" {
		cmd.Env = append(os.Environ(), "KUBECONFIG="+kubeconfigPath)
	}

	if namespace != "" {
		cmd.Args = append(cmd.Args, "-n", namespace)
	}

	fmt.Printf("[Jarvis] Launching k9s...\n")
	return cmd.Run()
}
