import socket
import sys
import time
import plotly.graph_objs as go
from geopy.geocoders import Nominatim
import requests

def get_geolocation(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=lat,lon,country,city")
        geo_data = response.json()
        return geo_data['lat'], geo_data['lon'], geo_data['country'], geo_data['city']
    except Exception as e:
        print(f"Geolocation lookup failed for {ip}: {e}")
        return None, None, None, None



def traceroute(dest_addr, dest_port, max_hops):
    ttl = 1
    trace_data = []

    while ttl <= max_hops:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # send socket
        icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_ICMP)  # receive socket
        
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

                lat, lon, country, city = get_geolocation(sender_ip)
                element = {
                    "ttl": ttl,
                    "host": host,
                    "ip": sender_ip,
                    "rtt": rtt,
                    "lat": lat,
                    "lon": lon,
                    "country": country,
                    "city": city
                }

                # May or may not be helpfull but sometimes bugged my Trace

                #if any(hop["ip"] == sender_ip for hop in trace_data):
                #    print(f"Duplicate IP found: {sender_ip}. Trace complete.")
                #    break

                trace_data.append(element)
                print(f"{ttl} - {host} ({sender_ip}) - {city}, {country} - RTT: {rtt:.2f} ms")

                if sender_ip == dest_addr:
                    print("Reached destination IP. Trace complete.")
                    break

            except socket.timeout:
                trace_data.append({
                    "ttl": ttl,
                    "host": "*",
                    "ip": "*",
                    "rtt": None,
                    "lat": None,
                    "lon": None,
                    "country": None,
                    "city": None
                })
                print(f"{ttl} - Timeout!!")

        finally:
            udp_socket.close()
            icmp_socket.close()

        ttl += 1

    return trace_data




def visualize_traceroute(trace_data, destination_host):
    # Filter out hops without valid geolocation
    trace_data = [hop for hop in trace_data if hop["lat"] is not None and hop["lon"] is not None]

    if len(trace_data) < 2:
        print("Not enough data to create a meaningful visualization.")
        return

    latitudes = [hop["lat"] for hop in trace_data]
    longitudes = [hop["lon"] for hop in trace_data]
    text = [f"TTL: {hop['ttl']}<br>Host: {hop['host']}<br>IP: {hop['ip']}<br>RTT: {hop['rtt']:.2f} ms<br>"
            f"Location: {hop['city']}, {hop['country']}"
            if hop["rtt"] is not None else f"TTL: {hop['ttl']}<br>Host: Timeout"
            for hop in trace_data]

    fig = go.Figure()

    # Add a trace for each segment
    for i in range(len(trace_data) - 1):
        fig.add_trace(go.Scattergeo(
            locationmode='ISO-3',
            lon=[longitudes[i], longitudes[i + 1]],
            lat=[latitudes[i], latitudes[i + 1]],
            mode='lines+markers',
            line=dict(width=2, color='blue'),
            marker=dict(size=6),
            text=[text[i], text[i + 1]],
            hoverinfo='text'
        ))

    fig.update_layout(
        title=f"Traceroute Visualizer. Destination: {destination_host}",
        showlegend=False,
        geo=dict(
            scope='world',
            projection=go.layout.geo.Projection(type='equirectangular'),
            showland=True,
            landcolor='rgb(243, 243, 243)',
            subunitwidth=1,
            countrywidth=1,
            subunitcolor="rgb(217, 217, 217)",
            countrycolor="rgb(217, 217, 217)"
        )
    )

    fig.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 traceroute.py <hostname>")
        sys.exit(1)

    dest_addr = socket.gethostbyname(sys.argv[1])
    dest_port = 33434
    max_hops = 15     # adjust as you wish, however I didn't feel the need

    trace_data = traceroute(dest_addr, dest_port, max_hops)
    visualize_traceroute(trace_data, sys.argv[1])



# a couple different URL's to try:
# www.google.com
# www.government.ru 
# www.tanzania.go.tz
