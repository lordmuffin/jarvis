package secrets

import (
	"bytes"
	"fmt"
	"os/exec"
	"strings"
)

// InjectSecrets runs a command with secrets injected via 'op run'
// This ensures secrets are never written to disk or exposed in the shell history directly.
func InjectSecrets(command []string) error {
	// Construct the command: op run -- <command>
	args := append([]string{"run", "--"}, command...)
	cmd := exec.Command("op", args...)
	cmd.Stdout = nil // Connect to stdout/stderr if needed, or capturing logic
	return cmd.Run()
}

// GetSecret retrieves a secret by reference `op://vault/item/field`
func GetSecret(reference string) (string, error) {
	cmd := exec.Command("op", "read", reference, "--no-newline")
	var out bytes.Buffer
	cmd.Stdout = &out
	err := cmd.Run()
	if err != nil {
		return "", fmt.Errorf("failed to read secret '%s': %w", reference, err)
	}
	return strings.TrimSpace(out.String()), nil
}
