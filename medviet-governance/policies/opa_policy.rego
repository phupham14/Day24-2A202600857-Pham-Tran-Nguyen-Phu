package medviet.data_access

import future.keywords.if
import future.keywords.in

# Default: deny all
default allow := false

# Admin được phép tất cả
allow if {
    input.user.role == "admin"
}

# ML Engineer được đọc training data và model artifacts
allow if {
    input.user.role == "ml_engineer"
    input.resource in {"training_data", "model_artifacts"}
    input.action in {"read", "write"}
}

# ML Engineer KHÔNG được delete production data — không có rule allow nên bị deny-by-default.
# Rule deny tường minh để audit log rõ ràng hơn.
deny if {
    input.user.role == "ml_engineer"
    input.resource == "production_data"
    input.action == "delete"
}

# Data Analyst chỉ được đọc aggregated metrics và viết reports
allow if {
    input.user.role == "data_analyst"
    input.resource == "aggregated_metrics"
    input.action == "read"
}

allow if {
    input.user.role == "data_analyst"
    input.resource == "reports"
    input.action == "write"
}

# Intern chỉ được access sandbox data (read/write), không access production
allow if {
    input.user.role == "intern"
    input.resource == "sandbox_data"
    input.action in {"read", "write"}
}

# Không ai được export restricted data ra ngoài VN servers
deny if {
    input.data_classification == "restricted"
    input.destination_country != "VN"
}

# Final decision: allow nếu có rule allow VÀ không có rule deny
final_allow if {
    allow
    not deny
}
