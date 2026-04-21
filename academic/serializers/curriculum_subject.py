from rest_framework import serializers
from academic.models import CurriculumSubject
from academic.models.curriculum import Curriculum
from academic.models.subject import Subject
from .curriculum import CurriculumMinimalSerializer
from .subject import SubjectMinimalSerializer


class CurriculumSubjectMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for curriculum subjects."""

    subject = SubjectMinimalSerializer(read_only=True)

    class Meta:
        model = CurriculumSubject
        fields = ["id", "subject", "year_level_order", "semester", "is_required"]
        read_only_fields = fields


class CurriculumSubjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding a subject to a curriculum."""

    curriculum_id = serializers.PrimaryKeyRelatedField(
        queryset=Curriculum.objects.all(), source="curriculum"
    )
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject"
    )

    class Meta:
        model = CurriculumSubject
        fields = ["curriculum_id", "subject_id", "year_level_order", "semester", "sequence", "is_required"]

    def create(self, validated_data) -> CurriculumSubject:
        from academic.services.curriculum_subject import CurriculumSubjectService

        return CurriculumSubjectService.add_subject_to_curriculum(**validated_data)


class CurriculumSubjectUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a curriculum subject entry."""

    class Meta:
        model = CurriculumSubject
        fields = ["year_level_order", "semester", "sequence", "is_required"]

    def update(self, instance, validated_data) -> CurriculumSubject:
        from academic.services.curriculum_subject import CurriculumSubjectService

        return CurriculumSubjectService.update_curriculum_subject(instance, validated_data)


class CurriculumSubjectDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a curriculum subject."""

    curriculum = CurriculumMinimalSerializer(read_only=True)
    subject = SubjectMinimalSerializer(read_only=True)

    class Meta:
        model = CurriculumSubject
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]