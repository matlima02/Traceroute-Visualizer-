import socket
import sys
import time

def traceroute(dest_addr, dest_port, max_hops):
    ttl = 1

    while ttl <= max_hops:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)                       # send socket
        icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_ICMP) # receive socket
        
        udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)    
        icmp_socket.settimeout(2)
        udp_socket.settimeout(2)

        try:
            message = ''
            udp_socket.sendto(message.encode('utf-8'), (dest_addr, dest_port))  

            try:
                start_time = time.time()
                response, where_from = icmp_socket.recvfrom(1024)
                end_time = time.time()
                
                sender_ip = where_from[0]
                rtt = (end_time - start_time) * 1000  

                try:
                    host = socket.gethostbyaddr(sender_ip)[0]   
                except socket.herror:
                    host = "*"

                print(f"{ttl} - {host} ({sender_ip}) - RTT: {rtt:.2f} ms")

                if sender_ip == dest_addr:
                    print("Trace complete.")
                    break

            except socket.timeout:
                print(f"{ttl} - Timeout!!")


        finally:
            udp_socket.close()
            icmp_socket.close()

        ttl += 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python traceroute.py <hostname>")
        sys.exit(1)

    dest_addr = socket.gethostbyname(sys.argv[1])
    dest_port = 33434
    max_hops = 30  

    traceroute(dest_addr, dest_port, max_hops)
