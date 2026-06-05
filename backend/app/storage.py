from supabase import create_client

from app.config import (
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_BUCKET,
)


if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing")

if not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY is missing")

if not SUPABASE_BUCKET:
    raise ValueError("SUPABASE_BUCKET is missing")


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
)


def get_storage_path(user_id: int, filename: str):
    return f"user_{user_id}/{filename}"


def upload_file_to_supabase(user_id: int, filename: str, file_path: str):
    storage_path = get_storage_path(user_id, filename)

    print("Uploading:", storage_path)

    with open(file_path, "rb") as file:
        response = supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=storage_path,
            file=file,
            file_options={
                "content-type": "application/pdf",
                "x-upsert": "true",
            },
        )

    print("Upload response:", response)

    return storage_path


def delete_file_from_supabase(user_id: int, filename: str):
    storage_path = get_storage_path(user_id, filename)

    print("Deleting:", storage_path)

    try:
        response = supabase.storage.from_(SUPABASE_BUCKET).remove(
            [storage_path]
        )
        print("Delete response:", response)
    except Exception as error:
        print("Storage delete error:", error)

    return storage_path

def get_signed_url(storage_path: str):
    response = (
        supabase.storage
        .from_(SUPABASE_BUCKET)
        .create_signed_url(
            storage_path,
            3600,  # 1 hour
        )
    )

    return response["signedURL"]