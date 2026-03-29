PLAN_LIMITS = {
    "starter": {
        "customers": 50,
        "services": 100,
        "users": 2,
    },
    "pro": {
        "customers": 500,
        "services": 1000,
        "users": 10,
    },
    "business": {
        "customers": None,
        "services": None,
        "users": None,
    },
}


def get_limit(company, key):
    plan = getattr(company, "plan", "starter")
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["starter"]).get(key)


def get_usage(company, model):
    from app.extensions import db
    return db.session.query(model).filter_by(company_id=company.id).count()


def is_limit_reached(company, model, key):
    limit = get_limit(company, key)

    if limit is None:
        return False

    usage = get_usage(company, model)
    return usage >= limit


def get_usage_data(company):
    from app.models.customer import Customer
    from app.models.service import Service
    from app.models.user import User

    data = {}

    for key, model in {
        "customers": Customer,
        "services": Service,
        "users": User,
    }.items():
        limit = get_limit(company, key)
        usage = get_usage(company, model)

        percent = int((usage / limit) * 100) if limit else 0

        data[key] = {
            "limit": limit,
            "usage": usage,
            "percent": percent,
        }

    return data
