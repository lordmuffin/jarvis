package lxc

import (
	"fmt"
	"os/exec"
)

// Runner handles LXC interactions
type Runner struct{}

// NewRunner creates a new LXC runner
func NewRunner() *Runner {
	return &Runner{}
}

// Bootstrap creates a new LXC container
func (r *Runner) Bootstrap(name, template string) error {
	fmt.Printf("[LXC] Bootstrapping container '%s' from template '%s'...\n", name, template)
	// Example command: lxc-create -t download -n name -- -d ubuntu -r jammy -a amd64
	// For simulation safely without running destructive commands:
	cmd := exec.Command("echo", "lxc-create", "-n", name, "-t", template)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("failed to bootstrap lxc: %w", err)
	}
	fmt.Printf("%s", string(out))
	return nil
}

// Snapshot takes a snapshot of the container
func (r *Runner) Snapshot(name string) error {
	fmt.Printf("[LXC] Snapshotting container '%s'...\n", name)
	cmd := exec.Command("echo", "lxc-snapshot", "-n", name)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("failed to snapshot lxc: %w", err)
	}
	fmt.Printf("%s", string(out))
	return nil
}

// Exec runs a command inside the container (bridge for CLI)
func (r *Runner) Exec(name string, command []string) error {
	args := append([]string{"lxc-attach", "-n", name, "--"}, command...)
	cmd := exec.Command(args[0], args[1:]...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return err
	}
	fmt.Println(string(out))
	return nil
}
