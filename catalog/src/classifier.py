"""Hybrid keyword classifier for catalog components.

Classifies components into project types and personas based on
substring matching against name, description, and tags.
"""

PROJECT_TYPE_KEYWORDS: dict[str, list[str]] = {
    "devops": [
        "terraform",
        "pulumi",
        "github-actions",
        "github actions",
        "ci/cd",
        "cicd",
        "pipeline",
        "helm",
        "argocd",
        "argo-cd",
        "ansible",
        "jenkins",
        "gitlab-ci",
        "gitlab ci",
        "infrastructure",
        "iac",
        "infra-as-code",
    ],
    "app-deploy": [
        "kubernetes",
        "k8s",
        "cloud-run",
        "cloudrun",
        "cloudflare",
        "docker",
        "container",
        "deployment",
        "ingress",
        "service-mesh",
        "istio",
        "envoy",
        "deploy",
        "pod",
        "replica",
        "microservice",
    ],
    "policy-as-code": [
        "kyverno",
        "opa",
        "rego",
        "gatekeeper",
        "sentinel",
        "policy",
        "compliance",
        "admission-controller",
        "admission controller",
        "governance",
        "audit",
    ],
    "docs": [
        "documentation",
        "mkdocs",
        "docusaurus",
        "sphinx",
        "readme",
        "confluence",
        "backstage",
        "catalog-info",
        "technical-writing",
        "docs-site",
        "adrs",
    ],
    "sales-marketing": [
        "presentation",
        "pitch",
        "proposal",
        "slide",
        "marketing",
        "campaign",
        "branding",
        "collateral",
        "demo",
        "sales",
        "prospect",
        "outreach",
    ],
    "big-data": [
        "dbt",
        "bigquery",
        "snowflake",
        "mongodb",
        "spark",
        "airflow",
        "dagster",
        "data-pipeline",
        "etl",
        "warehouse",
        "data-lake",
        "redshift",
        "parquet",
        "iceberg",
        "delta-lake",
        "fivetran",
        "stitch",
    ],
    "finops": [
        "cost",
        "billing",
        "budget",
        "finops",
        "pricing",
        "cloud-cost",
        "usage-report",
        "chargeback",
        "showback",
        "savings",
        "reserved-instance",
        "commitment",
        "spend",
    ],
}

PERSONA_KEYWORDS: dict[str, list[str]] = {
    "platform-engineer": [
        "platform",
        "self-service",
        "golden-path",
        "developer-experience",
        "internal-developer",
        "scaffold",
        "template",
        "backstage",
    ]
    + PROJECT_TYPE_KEYWORDS["devops"]
    + PROJECT_TYPE_KEYWORDS["app-deploy"],
    "cloud-sre": [
        "sre",
        "reliability",
        "incident",
        "on-call",
        "oncall",
        "monitoring",
        "observability",
        "slo",
        "sli",
        "error-budget",
        "pagerduty",
        "opsgenie",
        "alerting",
        "uptime",
    ]
    + PROJECT_TYPE_KEYWORDS["devops"],
    "data-engineer": [
        "data-engineer",
        "data engineer",
        "data-pipeline",
        "etl",
        "elt",
        "schema",
        "migration",
        "warehouse",
    ]
    + PROJECT_TYPE_KEYWORDS["big-data"],
    "ml-engineer": [
        "ml",
        "machine-learning",
        "model",
        "training",
        "inference",
        "feature-store",
        "mlops",
        "mlflow",
        "kubeflow",
        "sagemaker",
        "vertex-ai",
        "huggingface",
        "pytorch",
        "tensorflow",
    ],
    "sales": [
        "sales",
        "crm",
        "salesforce",
        "hubspot",
        "pipeline",
        "lead",
        "prospect",
        "deal",
        "quota",
        "forecast",
    ]
    + PROJECT_TYPE_KEYWORDS["sales-marketing"],
    "marketing": [
        "marketing",
        "campaign",
        "content",
        "seo",
        "analytics",
        "social-media",
        "brand",
        "creative",
    ]
    + PROJECT_TYPE_KEYWORDS["sales-marketing"],
    "accounting": [
        "accounting",
        "finance",
        "invoice",
        "ledger",
        "reconciliation",
        "tax",
        "audit",
        "compliance",
        "reporting",
    ]
    + PROJECT_TYPE_KEYWORDS["finops"],
    "director-vp": [
        "dashboard",
        "report",
        "summary",
        "overview",
        "metrics",
        "kpi",
        "executive",
        "strategy",
        "roadmap",
        "okr",
        "planning",
        "roi",
        "portfolio",
    ],
}


def keyword_classify(
    *, name: str, description: str, tags: list[str]
) -> dict[str, list[str]]:
    """Classify a component by substring-matching keywords.

    Builds searchable text from name + description + tags (lowercased),
    then checks each project type and persona keyword list for substring
    matches. A component can match multiple types and personas.

    Returns {"project_types": [...], "personas": [...]}.
    """
    # Normalize tags: may be None, a string, or a list from YAML frontmatter
    if tags is None:
        tags = []
    elif isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    else:
        tags = [str(t) for t in tags]
    searchable = " ".join([name or "", description or ""] + tags).lower()

    project_types: list[str] = []
    for slug, keywords in PROJECT_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in searchable:
                project_types.append(slug)
                break

    personas: list[str] = []
    for slug, keywords in PERSONA_KEYWORDS.items():
        for kw in keywords:
            if kw in searchable:
                personas.append(slug)
                break

    return {"project_types": sorted(project_types), "personas": sorted(personas)}


def merge_classifications(
    keyword_result: dict[str, list[str]],
    ai_result: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Merge keyword and AI classification results.

    Takes the union of both results. AI is additive and never removes
    keyword-matched tags.

    Returns sorted lists.
    """
    project_types = set(keyword_result.get("project_types", []))
    project_types |= set(ai_result.get("project_types", []))

    personas = set(keyword_result.get("personas", []))
    personas |= set(ai_result.get("personas", []))

    return {
        "project_types": sorted(project_types),
        "personas": sorted(personas),
    }
