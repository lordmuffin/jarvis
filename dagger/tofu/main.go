package main

import (
	"context"
)

type Tofu struct{}

// Plan runs 'tofu plan' and returns the plan output.
func (m *Tofu) Plan(
	ctx context.Context,
	source *Directory, // Directory containing .tf files
	// +optional
	vars []string, // List of -var "key=value" pairs
) (string, error) {
	container := dag.Container().
		From("ghcr.io/opentofu/opentofu:latest").
		WithDirectory("/src", source).
		WithWorkdir("/src").
		WithExec([]string{"tofu", "init"})

	args := []string{"tofu", "plan", "-no-color"}
	for _, v := range vars {
		args = append(args, "-var", v)
	}

	return container.WithExec(args).Stdout(ctx)
}

// Apply runs 'tofu apply' with auto-approval.
func (m *Tofu) Apply(
	ctx context.Context,
	source *Directory,
	// +optional
	vars []string,
) (string, error) {
	container := dag.Container().
		From("ghcr.io/opentofu/opentofu:latest").
		WithDirectory("/src", source).
		WithWorkdir("/src").
		WithExec([]string{"tofu", "init"})

	args := []string{"tofu", "apply", "-auto-approve", "-no-color"}
	for _, v := range vars {
		args = append(args, "-var", v)
	}

	return container.WithExec(args).Stdout(ctx)
}
