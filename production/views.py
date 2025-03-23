from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework.decorators import action

from common.core.filter import BaseFilterSet
from common.core.modelset import BaseModelSet, ImportExportDataAction
from common.core.pagination import DynamicPageNumber
from common.core.response import ApiResponse
from common.utils import get_logger
from production.models import ProductionOrder, ProductionReport, ProcessStep, Process, Workshop
from production.serializers.serializer import ProductionOrderSerializer, ProductionReportSerializer, \
    ProcessStepSerializer, ProcessSerializer, WorkshopSerializer

logger = get_logger(__name__)


class WorkshopFilter(BaseFilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Workshop
        fields = ['name', 'is_active']


class WorkshopViewSet(BaseModelSet, ImportExportDataAction):
    """生产车间"""
    queryset = Workshop.objects.all()
    serializer_class = WorkshopSerializer
    ordering_fields = ['pk', 'name']
    filterset_class = WorkshopFilter
    pagination_class = DynamicPageNumber(1000)


class ProcessFilter(BaseFilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    code = filters.CharFilter(field_name="code", lookup_expr="icontains")

    class Meta:
        model = Process
        fields = ['code', 'name', 'is_active']


class ProcessViewSet(BaseModelSet, ImportExportDataAction):
    """工艺流程"""
    queryset = Process.objects.all()
    serializer_class = ProcessSerializer
    ordering_fields = ['code', 'name']
    filterset_class = ProcessFilter
    pagination_class = DynamicPageNumber(1000)


class ProcessStepFilter(BaseFilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    code = filters.CharFilter(field_name="code", lookup_expr="icontains")
    process = filters.NumberFilter(field_name="process")

    class Meta:
        model = ProcessStep
        fields = ['code', 'name', 'is_active', 'process']


class ProcessStepViewSet(BaseModelSet, ImportExportDataAction):
    """工序管理"""
    queryset = ProcessStep.objects.all()
    serializer_class = ProcessStepSerializer
    ordering_fields = ["process", "order", "code"]
    filterset_class = ProcessStepFilter
    pagination_class = DynamicPageNumber(1000)


class ProductionOrderFilter(BaseFilterSet):
    order_number = filters.CharFilter(field_name="order_number", lookup_expr="icontains")
    production_number = filters.CharFilter(field_name="production_number", lookup_expr="icontains")
    product_name = filters.CharFilter(field_name="product_name", lookup_expr="icontains")
    workshop = filters.NumberFilter(field_name="workshop")
    process = filters.NumberFilter(field_name="process")
    status = filters.ChoiceFilter(field_name="status", choices=ProductionOrder.STATUS_CHOICES)
    order_date = filters.DateFromToRangeFilter(field_name="order_date")
    planned_start_date = filters.DateFromToRangeFilter(field_name="planned_start_date")
    planned_end_date = filters.DateFromToRangeFilter(field_name="planned_end_date")

    class Meta:
        model = ProductionOrder
        fields = ['order_number', 'production_number', 'product_name', 'workshop', 'process', 
                 'status', 'order_date', 'planned_start_date', 'planned_end_date']


class ProductionOrderViewSet(BaseModelSet, ImportExportDataAction):
    """生产工单"""
    queryset = ProductionOrder.objects.all()
    serializer_class = ProductionOrderSerializer
    ordering_fields = ['-order_date', 'order_number']
    filterset_class = ProductionOrderFilter
    pagination_class = DynamicPageNumber(1000)

    @action(methods=['post'], detail=True)
    def cancel(self, request, *args, **kwargs):
        """取消工单"""
        instance = self.get_object()
        if instance.status in ['pending', 'in_progress']:
            instance.status = 'canceled'
            instance.save(update_fields=['status'])
            return ApiResponse(detail=f"工单 {instance.order_number} 已取消")
        return ApiResponse(code=400, detail="只有待生产或生产中的工单可以取消")


class ProductionReportFilter(BaseFilterSet):
    production_order = filters.NumberFilter(field_name="production_order")
    process_step = filters.NumberFilter(field_name="process_step")
    start_time = filters.DateTimeFromToRangeFilter(field_name="start_time")
    end_time = filters.DateTimeFromToRangeFilter(field_name="end_time")
    creator = filters.NumberFilter(field_name="creator")

    class Meta:
        model = ProductionReport
        fields = ['production_order', 'process_step', 'start_time', 'end_time', 'creator', 'created_time']


class ProductionReportViewSet(BaseModelSet, ImportExportDataAction):
    """生产报工"""
    queryset = ProductionReport.objects.all()
    serializer_class = ProductionReportSerializer
    ordering_fields = ['-created_time', 'production_order']
    filterset_class = ProductionReportFilter
    pagination_class = DynamicPageNumber(1000)

    @action(methods=['post'], detail=True)
    def complete(self, request, *args, **kwargs):
        """完成报工"""
        instance = self.get_object()
        if not instance.end_time:
            instance.end_time = timezone.now()
            instance.save()
            return ApiResponse(detail=f"报工 {instance.production_order.order_number}-{instance.process_step.name} 已完成")
        return ApiResponse(code=400, detail="该报工已经完成")

    @action(methods=['post'], detail=True)
    def pause(self, request, *args, **kwargs):
        """暂停报工"""
        instance = self.get_object()
        if not instance.end_time and not instance.pause_time:
            instance.pause_time = timezone.now()
            instance.save()
            return ApiResponse(detail=f"报工 {instance.production_order.order_number}-{instance.process_step.name} 已暂停")
        return ApiResponse(code=400, detail="该报工已完成或已暂停")

    @action(methods=['post'], detail=True)
    def resume(self, request, *args, **kwargs):
        """恢复报工"""
        instance = self.get_object()
        if instance.pause_time and not instance.resume_time and not instance.end_time:
            instance.resume_time = timezone.now()
            instance.save()
            return ApiResponse(detail=f"报工 {instance.production_order.order_number}-{instance.process_step.name} 已恢复")
        return ApiResponse(code=400, detail="该报工未暂停或已完成")
