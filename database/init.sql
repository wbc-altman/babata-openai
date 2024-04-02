create extension if not exists "uuid-ossp";

CREATE TABLE "public"."t_account"
(
    "id"         serial PRIMARY KEY,
    "uuid"       uuid                 DEFAULT uuid_generate_v4(),

    "username"   varchar     NOT NULL,
    "password"   varchar     NOT NULL,

    "meta_info"  jsonb       NOT NULL DEFAULT '{}',
    "created_at" timestamptz NOT NULL DEFAULT now(),
    "updated_at" timestamptz NOT NULL DEFAULT now(),
    "deleted_at" timestamptz
);
