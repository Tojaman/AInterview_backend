from drf_yasg import openapi

get_params = [
	openapi.Parameter(
        "변환된 텍스트", # 파라미터 명칭
        openapi.IN_QUERY,
        description="음성 파일을 txt로 변환한다.", # 설명
        type=openapi.FORMAT_DATE,
        default=""
    ),
    openapi.Parameter(
        "테스트",
        openapi.IN_QUERY,
        description="테스트중",
        type=openapi.FORMAT_DATE,
        default=""
    )
]

post_params = openapi.Schema(
    type=openapi.TYPE_OBJECT, 
    properties={
        'x': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
        'y': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
    }
)