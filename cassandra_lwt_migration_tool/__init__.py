import logging

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)

logging.basicConfig(handlers=[console])
