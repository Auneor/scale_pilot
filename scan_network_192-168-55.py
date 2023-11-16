import concurrent.futures
import os


def ping_ip(ip):
    response = os.system("ping -c 1 -W 2 " + ip + " > /dev/null 2>&1")
    return ip if response == 0 else None


subnet = "192.168.55"
reachable_ips = []

# We'll use a with statement to ensure threads are cleaned up promptly
with concurrent.futures.ThreadPoolExecutor(max_workers=255) as executor:
    # Start the load operations and mark each future with its IP
    future_to_ip = {
        executor.submit(ping_ip, f"{subnet}.{i}"): str(i) for i in range(1, 256)
    }
    for future in concurrent.futures.as_completed(future_to_ip):
        ip = future_to_ip[future]
        try:
            data = future.result()
        except Exception as exc:
            print("%r generated an exception: %s" % (ip, exc))
        else:
            if data is not None:  # only append the reachable ip addresses.
                reachable_ips.append(data)

print("Reachable IPs:")
for ip in reachable_ips:
    print(ip)
