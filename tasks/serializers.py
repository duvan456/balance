from django.conf import settings
from rest_framework import serializers

from .models import Task
from .source_registry import SUPPORTED_DATE_TYPES, resolve_rubro_interval_coverage


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MovementSortSerializer(serializers.Serializer):
    field = serializers.ChoiceField(
        choices=[
            "accounting_date",
            "accounting_value_date",
            "rubro",
            "rubro_description",
            "customer_account",
            "nit",
            "amount",
            "operation_type",
            "branch",
            "cost_center",
            "source_currency",
        ]
    )
    direction = serializers.ChoiceField(choices=["asc", "desc"])


class MovementQuerySerializer(serializers.Serializer):
    date_type = serializers.ChoiceField(choices=sorted(SUPPORTED_DATE_TYPES.keys()))
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    initial_rubro = serializers.IntegerField(min_value=0)
    final_rubro = serializers.IntegerField(min_value=0)
    customer_account = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=0,
        max_value=9223372036854775807,
    )
    nit = serializers.CharField(required=False, allow_blank=True, allow_null=True, trim_whitespace=True)
    branch = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, default=100)
    sorting = serializers.ListField(
        child=MovementSortSerializer(),
        required=False,
        allow_empty=True,
        default=list,
    )

    def validate(self, attrs):
        if attrs["date_from"] > attrs["date_to"]:
            raise serializers.ValidationError({"date_from": "date_from cannot be greater than date_to."})

        if attrs["initial_rubro"] > attrs["final_rubro"]:
            raise serializers.ValidationError({"initial_rubro": "initial_rubro cannot be greater than final_rubro."})

        max_page_size = getattr(settings, "MOVEMENT_PAGE_SIZE_MAX", 100)
        if attrs["page_size"] > max_page_size:
            raise serializers.ValidationError({"page_size": f"page_size cannot exceed {max_page_size}."})

        coverage = resolve_rubro_interval_coverage(attrs["initial_rubro"], attrs["final_rubro"])
        if coverage["uncovered"]:
            ranges = ", ".join(
                f"{segment['start']}-{segment['end']}" for segment in coverage["uncovered"]
            )
            raise serializers.ValidationError(
                {
                    "initial_rubro": (
                        "The requested rubro range includes unsupported intervals: "
                        f"{ranges}."
                    )
                }
            )

        if attrs.get("nit") is not None and not isinstance(attrs["nit"], str):
            raise serializers.ValidationError({"nit": "NIT must be treated as text."})

        return attrs
