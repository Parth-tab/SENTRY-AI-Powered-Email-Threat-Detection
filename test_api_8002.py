import httpx

r_seed = httpx.post('http://localhost:8002/api/v1/samples/seed')
print("Seed status:", r_seed.status_code)

r = httpx.get('http://localhost:8002/api/v1/emails')
emails = r.json()
print("Emails count:", len(emails))
first_id = emails[0]['id']
print("First ID:", first_id)
r_detail = httpx.get(f'http://localhost:8002/api/v1/emails/{first_id}')
print("Detail status:", r_detail.status_code)
if r_detail.status_code == 200:
    data = r_detail.json()
    print("Subject:", data['email']['subject'])
    print("Origin IP:", data['analysis']['origin_assessment']['probable_origin_ip'])
    print("Hops:", len(data['analysis']['relay_path']))
else:
    print("Detail error:", r_detail.text)
