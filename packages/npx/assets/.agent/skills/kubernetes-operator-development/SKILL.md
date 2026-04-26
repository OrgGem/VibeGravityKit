---
name: kubernetes-operator-development
description: "Kubernetes operator and CRD development using controller-runtime and kubebuilder. Use for building custom controllers, CRDs, and automation for Kubernetes-native applications."
user-invocable: true
risk: safe
---

# Kubernetes Operator Development

Build production Kubernetes operators — Custom Resource Definitions (CRDs) and controllers using kubebuilder and controller-runtime.

## When to Use
- Creating a Custom Resource Definition (CRD) for a new Kubernetes resource
- Building a controller to automate operational tasks
- Implementing reconciliation loops for stateful applications
- Extending Kubernetes API with domain-specific resources

## Setup with Kubebuilder

```bash
# Install kubebuilder
curl -L -o kubebuilder https://go.kubebuilder.io/dl/latest/$(go env GOOS)/$(go env GOARCH)
chmod +x kubebuilder && mv kubebuilder /usr/local/bin/

# Bootstrap operator
kubebuilder init --domain example.com --repo github.com/org/myoperator
kubebuilder create api --group apps --version v1alpha1 --kind MyApp
```

## CRD Definition

```go
// api/v1alpha1/myapp_types.go
type MyAppSpec struct {
    Replicas int32  `json:"replicas,omitempty"`
    Image    string `json:"image"`
    // +kubebuilder:validation:Minimum=1
    // +kubebuilder:validation:Maximum=10
    MaxRetries int32 `json:"maxRetries,omitempty"`
}

type MyAppStatus struct {
    // +patchMergeKey=type
    // +patchStrategy=merge
    Conditions []metav1.Condition `json:"conditions,omitempty"`
    ReadyReplicas int32            `json:"readyReplicas,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="Replicas",type="integer",JSONPath=".spec.replicas"
// +kubebuilder:printcolumn:name="Ready",type="integer",JSONPath=".status.readyReplicas"
type MyApp struct {
    metav1.TypeMeta   `json:",inline"`
    metav1.ObjectMeta `json:"metadata,omitempty"`
    Spec   MyAppSpec   `json:"spec,omitempty"`
    Status MyAppStatus `json:"status,omitempty"`
}
```

## Reconciler

```go
// internal/controller/myapp_controller.go
func (r *MyAppReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    log := log.FromContext(ctx)

    // Fetch the resource
    app := &appsv1alpha1.MyApp{}
    if err := r.Get(ctx, req.NamespacedName, app); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }

    // Check deletion
    if !app.DeletionTimestamp.IsZero() {
        return r.handleDeletion(ctx, app)
    }

    // Add finalizer
    if !controllerutil.ContainsFinalizer(app, myFinalizer) {
        controllerutil.AddFinalizer(app, myFinalizer)
        return ctrl.Result{}, r.Update(ctx, app)
    }

    // Reconcile desired state
    if err := r.reconcileDeployment(ctx, app); err != nil {
        meta.SetStatusCondition(&app.Status.Conditions, metav1.Condition{
            Type:    "Ready",
            Status:  metav1.ConditionFalse,
            Reason:  "ReconcileError",
            Message: err.Error(),
        })
        _ = r.Status().Update(ctx, app)
        return ctrl.Result{RequeueAfter: 30 * time.Second}, err
    }

    meta.SetStatusCondition(&app.Status.Conditions, metav1.Condition{
        Type:   "Ready",
        Status: metav1.ConditionTrue,
        Reason: "Reconciled",
    })
    return ctrl.Result{}, r.Status().Update(ctx, app)
}
```

## Controller Setup

```go
func (r *MyAppReconciler) SetupWithManager(mgr ctrl.Manager) error {
    return ctrl.NewControllerManagedBy(mgr).
        For(&appsv1alpha1.MyApp{}).
        Owns(&appsv1.Deployment{}).
        Owns(&corev1.Service{}).
        WithOptions(controller.Options{MaxConcurrentReconciles: 3}).
        Complete(r)
}
```

## Best Practices
- **Idempotent reconciliation**: Always reconcile toward desired state, not react to events
- **Use Status subresource**: Never write status in the main resource update
- **Finalizers**: Add before creating external resources, remove after cleanup
- **Owner references**: Set on child resources so GC cleans them automatically
- **Requeue with backoff**: Use `ctrl.Result{RequeueAfter: duration}` for retries
- **Conditions**: Follow Kubernetes condition conventions (type, status, reason, message)
