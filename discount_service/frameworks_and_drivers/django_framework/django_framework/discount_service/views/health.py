from adrf.requests import AsyncRequest
from adrf.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    async def get(self, request: AsyncRequest, *args, **kwargs) -> Response:
        result = {
            "status": "Discount service responded with 200 OK",
        }

        return Response(result)
