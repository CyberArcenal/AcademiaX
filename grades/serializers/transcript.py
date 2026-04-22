from rest_framework import serializers
from grades.models import Transcript
from students.models.student import Student
from students.serializers.student import StudentMinimalSerializer


class TranscriptMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for transcripts."""

    student = StudentMinimalSerializer(read_only=True)

    class Meta:
        model = Transcript
        fields = ["id", "student", "cumulative_gwa", "graduation_date", "is_official"]
        read_only_fields = fields


class TranscriptCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a transcript."""

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source="student"
    )

    class Meta:
        model = Transcript
        fields = ["student_id", "cumulative_gwa", "total_units_completed", "graduation_date", "is_official", "notes", "pdf_url"]

    def create(self, validated_data) -> Transcript:
        from grades.services.transcript import TranscriptService

        return TranscriptService.create_transcript(**validated_data)


class TranscriptUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a transcript."""

    class Meta:
        model = Transcript
        fields = ["cumulative_gwa", "total_units_completed", "graduation_date", "is_official", "notes", "pdf_url"]

    def update(self, instance, validated_data) -> Transcript:
        from grades.services.transcript import TranscriptService

        return TranscriptService.update_transcript(instance, validated_data)


class TranscriptDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a transcript."""

    student = StudentMinimalSerializer(read_only=True)

    class Meta:
        model = Transcript
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "generated_at"]