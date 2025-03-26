from django.db import models
from django.utils import timezone

from common.core.models import DbBaseModel, DbAuditModel


class Workshop(DbBaseModel):
    """车间管理"""
    name = models.CharField(max_length=50, unique=True, verbose_name="车间名称")
    is_active = models.BooleanField(verbose_name="是否启用", default=True)

    class Meta:
        verbose_name = "车间管理"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Process(DbBaseModel):
    """工艺管理"""

    code = models.CharField(max_length=50, verbose_name="工艺编号", unique=True, db_index=True)
    name = models.CharField(max_length=100, verbose_name="工艺名称")
    is_active = models.BooleanField(verbose_name="是否启用", default=True)

    class Meta:
        verbose_name = "工艺管理"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.name}({self.code})"


class ProcessStep(DbBaseModel):
    """工序管理"""
    code = models.CharField(max_length=50, verbose_name="工序编号", unique=True, db_index=True)
    name = models.CharField(max_length=100, verbose_name="工序名称")
    process = models.ForeignKey(Process, on_delete=models.CASCADE, verbose_name="所属工艺", related_name="steps")
    order = models.IntegerField(default=0, verbose_name="工序顺序")
    is_active = models.BooleanField(verbose_name="是否启用", default=True)

    class Meta:
        verbose_name = "工序管理"
        verbose_name_plural = verbose_name
        ordering = ("process", "order")

    def __str__(self):
        return f"{self.name}({self.code})"


class ProductionOrder(DbBaseModel):
    """生产工单"""
    STATUS_CHOICES = (
        ('pending', '待生产'),
        ('in_progress', '生产中'),
        ('completed', '已完成'),
        ('canceled', '已取消'),
    )

    order_date = models.DateField(default=timezone.now, verbose_name="制单日期")
    order_number = models.CharField(max_length=50, unique=True, db_index=True, verbose_name="单据编号")
    production_number = models.CharField(max_length=50, db_index=True, verbose_name="生产令号")
    product_name = models.CharField(max_length=200, verbose_name="存货全称")
    process = models.ForeignKey(Process, on_delete=models.PROTECT, verbose_name="工艺流程",
                                limit_choices_to={'is_active': True})
    planned_start_date = models.DateField(verbose_name="计划开工日期")
    planned_end_date = models.DateField(verbose_name="计划完工日期")
    workshop = models.ForeignKey(Workshop, on_delete=models.PROTECT, verbose_name="生产车间")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="状态")

    class Meta:
        verbose_name = "生产工单"
        verbose_name_plural = verbose_name
        ordering = ("-order_date",)

    def __str__(self):
        return f"{self.order_number}-{self.product_name}"


class ProductionReport(DbAuditModel):
    """生产报工"""
    production_order = models.ForeignKey(
        ProductionOrder, on_delete=models.CASCADE, verbose_name="生产工单",
        limit_choices_to={'status__in': ['pending', 'in_progress']}
    )
    process_step = models.ForeignKey(ProcessStep, on_delete=models.CASCADE, verbose_name="工序")
    start_time = models.DateTimeField(verbose_name="开始时间")
    pause_time = models.DateTimeField(null=True, blank=True, verbose_name="暂停时间")
    resume_time = models.DateTimeField(null=True, blank=True, verbose_name="恢复时间")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")
    total_time = models.DurationField(null=True, blank=True, verbose_name="累计时间")

    class Meta:
        verbose_name = "生产报工"
        verbose_name_plural = verbose_name
        ordering = ("-created_time",)

    def __str__(self):
        return f"{self.production_order.order_number}-{self.process_step.name}"

    def check_completed(self):
        """检查报工是否已完成"""
        if self.total_time is not None:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("已完成的报工不允许再次操作")

    def delete(self, *args, **kwargs):
        # 当total_time不为null时，不允许删除
        self.check_completed()
        return super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        # 如果是已存在的记录且total_time不为null，则不允许编辑
        if self.pk:
            original = ProductionReport.objects.get(pk=self.pk)
            if original.total_time is not None:
                self.check_completed()

        if self.end_time and self.start_time:
            total = self.end_time - self.start_time
            if self.pause_time and self.resume_time:
                total -= (self.resume_time - self.pause_time)
            self.total_time = total

            # 检查所有工序是否已完成
            has_unfinished_steps = self.production_order.process.steps.filter(is_active=True).exclude(
                id__in=ProductionReport.objects.filter(
                    production_order=self.production_order,
                    end_time__isnull=False
                ).values_list("process_step_id", flat=True)
            ).exists()

            if not has_unfinished_steps:
                self.production_order.status = 'completed'
            elif self.production_order.status == 'pending':
                self.production_order.status = 'in_progress'

            self.production_order.save(update_fields=['status'])

        super().save(*args, **kwargs)
