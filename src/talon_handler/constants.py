# Mapping of common Homelab ports to service names
COMMON_SERVICES = {
    80: "HTTP",
    443: "HTTPS",
    22: "SSH",
    8096: "Jellyfin",
    8920: "Jellyfin (HTTPS)",
    32400: "Plex",
    8123: "Home Assistant",
    3000: "Homarr / Grafana",
    9000: "Portainer",
    8080: "Web Service / Traefik",
    2342: "DizqueTV",
    5000: "Synology / Flask",
    5055: "Overseerr",
    7878: "Radarr",
    8989: "Sonarr",
    8686: "Lidarr",
    9117: "Jackett",
    53: "DNS (Pi-hole/AdGuard)",
}

CONFIG_FILE = "talon_config.json"
DASHBOARD_FILE = "talon_dashboard.md"
PID_FILE = "talon.pid"
