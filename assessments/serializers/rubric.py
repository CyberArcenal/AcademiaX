from rest_framework import serializers
from assessments.models import RubricCriterion, RubricLevel
from assessments.models.assessment import Assessment
from .assessment import AssessmentMinimalSerializer


# RubricCriterion serializers
class RubricCriterionMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for rubric criteria."""

    assessment = AssessmentMinimalSerializer(read_only=True)

    class Meta:
        model = RubricCriterion
        fields = ["id", "assessment", "name", "max_points", "order"]
        read_only_fields = fields


class RubricCriterionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a rubric criterion."""

    assessment_id = serializers.PrimaryKeyRelatedField(
        queryset=Assessment.objects.all(), source="assessment"
    )

    class Meta:
        model = RubricCriterion
        fields = "__all__"

    def create(self, validated_data) -> RubricCriterion:
        from assessments.services.rubric import RubricCriterionService

        return RubricCriterionService.create_criterion(**validated_data)


class RubricCriterionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a rubric criterion."""

    class Meta:
        model = RubricCriterion
        fields = ["name", "description", "max_points", "order"]

    def update(self, instance, validated_data) -> RubricCriterion:
        from assessments.services.rubric import RubricCriterionService

        return RubricCriterionService.update_criterion(instance, validated_data)


class RubricCriterionDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a rubric criterion."""

    assessment = AssessmentMinimalSerializer(read_only=True)

    class Meta:
        model = RubricCriterion
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


# RubricLevel serializers
class RubricLevelMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for rubric levels."""

    class Meta:
        model = RubricLevel
        fields = ["id", "level_name", "points"]
        read_only_fields = fields


class RubricLevelCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a rubric level."""

    criterion_id = serializers.PrimaryKeyRelatedField(
        queryset=RubricCriterion.objects.all(), source="criterion"
    )

    class Meta:
        model = RubricLevel
        fields = "__all__"

    def create(self, validated_data) -> RubricLevel:
        from assessments.services.rubric import RubricLevelService

        return RubricLevelService.create_level(**validated_data)


class RubricLevelUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a rubric level."""

    class Meta:
        model = RubricLevel
        fields = ["level_name", "description", "points"]

    def update(self, instance, validated_data) -> RubricLevel:
        from assessments.services.rubric import RubricLevelService

        return RubricLevelService.update_level(instance, validated_data)


class RubricLevelDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a rubric level."""

    class Meta:
        model = RubricLevel
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]