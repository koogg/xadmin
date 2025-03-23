from rest_framework.routers import SimpleRouter

from production.views import (
    WorkshopViewSet, ProcessViewSet, ProcessStepViewSet,
    ProductionOrderViewSet, ProductionReportViewSet
)

app_name = 'production'

router = SimpleRouter(False)  # 设置为 False ,为了去掉url后面的斜线

router.register('workshop', WorkshopViewSet, basename='workshop')
router.register('process', ProcessViewSet, basename='process')
router.register('process-step', ProcessStepViewSet, basename='process-step')
router.register('production-order', ProductionOrderViewSet, basename='production-order')
router.register('production-report', ProductionReportViewSet, basename='production-report')

urlpatterns = [
]
urlpatterns += router.urls