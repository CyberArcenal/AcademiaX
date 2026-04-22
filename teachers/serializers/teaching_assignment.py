from rest_framework import serializers
from academic.models.subject import Subject
from classes.models.academic_year import AcademicYear
from classes.models.section import Section
from classes.models.term import Term
from teachers.models import TeachingAssignment
from teachers.models.teacher import Teacher
from .teacher import TeacherMinimalSerializer


class TeachingAssignmentMinimalSerializer(serializers.ModelSerializer):
    """Lightweight list view for teaching assignments."""

    teacher = TeacherMinimalSerializer(read_only=True)
    section = serializers.SerializerMethodField()
    subject = serializers.SerializerMethodField()
    academic_year = serializers.SerializerMethodField()
    term = serializers.SerializerMethodField()

    class Meta:
        model = TeachingAssignment
        fields = ["id", "teacher", "section", "subject", "academic_year", "term", "is_active"]
        read_only_fields = fields

    def get_section(self, obj):
        if obj.section:
            from classes.serializers.section import SectionMinimalSerializer
            return SectionMinimalSerializer(obj.section).data
        return None

    def get_subject(self, obj):
        if obj.subject:
            from academic.serializers.subject import SubjectMinimalSerializer
            return SubjectMinimalSerializer(obj.subject).data
        return None

    def get_academic_year(self, obj):
        if obj.academic_year:
            from classes.serializers.academic_year import AcademicYearMinimalSerializer
            return AcademicYearMinimalSerializer(obj.academic_year).data
        return None

    def get_term(self, obj):
        if obj.term:
            from classes.serializers.term import TermMinimalSerializer
            return TermMinimalSerializer(obj.term).data
        return None


class TeachingAssignmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a teaching assignment."""

    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source="teacher"
    )
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), source="section"
    )
    subject_id = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), source="subject"
    )
    academic_year_id = serializers.PrimaryKeyRelatedField(
        queryset=AcademicYear.objects.all(), source="academic_year"
    )
    term_id = serializers.PrimaryKeyRelatedField(
        queryset=Term.objects.all(), source="term", required=False, allow_null=True
    )

    class Meta:
        model = TeachingAssignment
        fields = ["teacher_id", "section_id", "subject_id", "academic_year_id", "term_id", "is_active"]

    def create(self, validated_data) -> TeachingAssignment:
        from teachers.services.teaching_assignment import TeachingAssignmentService
        return TeachingAssignmentService.create_assignment(**validated_data)


class TeachingAssignmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a teaching assignment."""

    class Meta:
        model = TeachingAssignment
        fields = ["is_active"]

    def update(self, instance, validated_data) -> TeachingAssignment:
        from teachers.services.teaching_assignment import TeachingAssignmentService
        return TeachingAssignmentService.update_assignment(instance, validated_data)


class TeachingAssignmentDisplaySerializer(serializers.ModelSerializer):
    """Detailed view for a teaching assignment."""

    teacher = TeacherMinimalSerializer(read_only=True)
    section = serializers.SerializerMethodField()
    subject = serializers.SerializerMethodField()
    academic_year = serializers.SerializerMethodField()
    term = serializers.SerializerMethodField()

    class Meta:
        model = TeachingAssignment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_section(self, obj):
        if obj.section:
            from classes.serializers.section import SectionMinimalSerializer
            return SectionMinimalSerializer(obj.section).data
        return None

    def get_subject(self, obj):
        if obj.subject:
            from academic.serializers.subject import SubjectMinimalSerializer
            return SubjectMinimalSerializer(obj.subject).data
        return None

    def get_academic_year(self, obj):
        if obj.academic_year:
            from classes.serializers.academic_year import AcademicYearMinimalSerializer
            return AcademicYearMinimalSerializer(obj.academic_year).data
        return None

    def get_term(self, obj):
        if obj.term:
            from classes.serializers.term import TermMinimalSerializer
            return TermMinimalSerializer(obj.term).data
        return None