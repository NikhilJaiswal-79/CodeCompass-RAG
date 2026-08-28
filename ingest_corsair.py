from ingestion import process_repo

print("Starting ingestion for corsairdev/corsair...")
process_repo("https://github.com/corsairdev/corsair", "corsairdev-corsair")
print("Ingestion complete!")
