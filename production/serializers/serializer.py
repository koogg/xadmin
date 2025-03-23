from rest_framework import serializers

from common.core.serializers import BaseModelSerializer
from common.fields.utils import input_wrapper
from production import models


class WorkshopSerializer(BaseModelSerializer):
    block = input_wrapper(serializers.SerializerMethodField)(read_only=True, input_type='boolean',
                                                            label="是否启用状态")

    class Meta:
        model = models.Workshop
        fields = ['pk', 'name', 'is_active', 'block']
        table_fields = ['pk', 'name', 'is_active']
        read_only_fields = ['pk']

    def get_block(self, obj):
        return obj.is_active


class ProcessSerializer(BaseModelSerializer):
    block = input_wrapper(serializers.SerializerMethodField)(read_only=True, input_type='boolean',
                                                            label="是否启用状态")

    class Meta:
        model = models.Process
        fields = ['pk', 'code', 'name', 'is_active', 'block']
        table_fields = ['pk', 'code', 'name', 'is_active']
        read_only_fields = ['pk']

    def get_block(self, obj):
        return obj.is_active


class ProcessStepSerializer(BaseModelSerializer):
    block = input_wrapper(serializers.SerializerMethodField)(read_only=True, input_type='boolean',
                                                            label="是否启用状态")

    class Meta:
        model = models.ProcessStep
        fields = ['pk', 'code', 'name', 'is_active', 'process', 'order', 'block']
        table_fields = ['pk', 'code', 'name', 'process', 'order', 'is_active']
        read_only_fields = ['pk']
        extra_kwargs = {
            'process': {
                'attrs': ['pk', 'name', 'code'], 'required': True, 'format': "{name}({code})",
            }
        }

    def get_block(self, obj):
        return obj.is_active


class ProductionOrderSerializer(BaseModelSerializer):
    # 修改日期字段的自定义处理，增加更多输入格式支持
    order_date = serializers.DateField(format="%Y-%m-%d", 
                                      input_formats=['%Y-%m-%d', 'iso-8601', '%Y-%m-%d %H:%M:%S'])
    planned_start_date = serializers.DateField(format="%Y-%m-%d", 
                                              input_formats=['%Y-%m-%d', 'iso-8601', '%Y-%m-%d %H:%M:%S'])
    planned_end_date = serializers.DateField(format="%Y-%m-%d", 
                                            input_formats=['%Y-%m-%d', 'iso-8601', '%Y-%m-%d %H:%M:%S'])

    class Meta:
        model = models.ProductionOrder
        fields = ['pk', 'order_date', 'order_number', 'production_number', 'product_name', 'planned_start_date',
                  'planned_end_date', 'status', 'workshop', 'process']
        table_fields = ['pk', 'order_number', 'production_number', 'product_name', 'workshop', 'process', 
                       'planned_start_date', 'planned_end_date', 'status']
        read_only_fields = ['pk']
        extra_kwargs = {
            'workshop': {
                'attrs': ['pk', 'name'], 'required': True, 'format': "{name}",
            },
            'process': {
                'attrs': ['pk', 'name', 'code'], 'required': True, 'format': "{name}({code})",
            }
        }


class ProductionReportSerializer(BaseModelSerializer):
    class Meta:
        model = models.ProductionReport
        fields = ['pk', 'production_order', 'process_step', 'start_time', 'end_time', 'resume_time', 'pause_time',
                  'total_time', 'creator_id', 'created_time', 'updated_time']
        table_fields = ['pk', 'production_order', 'process_step', 'start_time', 'end_time', 'total_time', 'creator_id']
        read_only_fields = ['pk', 'total_time', 'creator_id', 'created_time', 'updated_time']
        extra_kwargs = {
            'production_order': {
                'attrs': ['pk', 'order_number', 'product_name'], 'required': True, 
                'format': "{order_number}-{product_name}",
            },
            'process_step': {
                'attrs': ['pk', 'name', 'code'], 'required': True, 'format': "{name}({code})",
            }
        }
